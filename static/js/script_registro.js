document.addEventListener('DOMContentLoaded', function() {
    // Guarda de segurança: roda apenas se o formulário existir na página
    const projectForm = document.getElementById('project-form');

    // Lógica do modal (se existir na página Kanban)
    const modal = document.getElementById('projectModal');
    const openBtn = document.getElementById('openProjectModal');
    const closeBtn = document.getElementById('closeProjectModal');

    if (modal && openBtn && closeBtn) {
        openBtn.addEventListener('click', () => modal.classList.remove('hidden'));
        closeBtn.addEventListener('click', () => modal.classList.add('hidden'));
        modal.addEventListener('click', (e) => { if (e.target === modal) modal.classList.add('hidden'); });
    }

    if (!projectForm) return; // nada para fazer se o formulário não está na página

    const statusLabel = document.getElementById('status-label');
    const startButton = document.getElementById('start-button');
    
    // Botão customizado para o DEIP
    const deipButton = document.getElementById('deip-button');
    const deipInput = document.getElementById('deip_pdf');
    const deipFilename = document.getElementById('deip-filename');

    if (deipButton && deipInput) {
        // Flag global do fluxo de escolha de arquivo
        if (!window.__deipPicking) window.__deipPicking = false;

        // Evita bind duplo em caso de script carregado duas vezes
        if (!deipButton.dataset.bound) {
            deipButton.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                if (window.__deipPicking) return; // já está abrindo o seletor
                window.__deipPicking = true;
                // Reset para garantir que selecionar o mesmo arquivo dispare 'change'
                deipInput.value = '';
                deipInput.click();
            });
            deipButton.dataset.bound = '1';
        }
        if (!deipInput.dataset.bound) {
            // Impede propagação de eventos a ancestrais (modal, etc.)
            deipInput.addEventListener('click', (e) => {
                e.stopPropagation();
                e.stopImmediatePropagation();
            });
            // Alguns navegadores disparam 'cancel' quando o diálogo é fechado sem seleção
            deipInput.addEventListener('cancel', () => { window.__deipPicking = false; });

            deipInput.addEventListener('change', () => {
                window.__deipPicking = false;
                if (deipInput.files.length > 0) {
                    const filename = deipInput.files[0].name;
                    deipFilename.textContent = `Arquivo selecionado: ${filename}`;
                    deipButton.style.backgroundColor = 'var(--success-color)';
                    deipButton.textContent = 'DEIP Selecionado';
                } else {
                    deipFilename.textContent = '';
                    deipButton.style.backgroundColor = 'var(--primary-color)';
                    deipButton.textContent = 'Selecionar DEIP (.pdf)...';
                }
            });
            deipInput.dataset.bound = '1';
        }
    }

    // Mostrar/esconder opções de importação e integração
    const importacaoRadios = document.querySelectorAll('input[name="importacao"]');
    const integracaoRadios = document.querySelectorAll('input[name="integracao"]');
    const importacaoOptions = document.getElementById('importacao-options');
    const integracaoOptions = document.getElementById('integracao-options');

    importacaoRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (importacaoOptions) importacaoOptions.classList.toggle('hidden', e.target.value !== 's');
        });
    });

    integracaoRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (integracaoOptions) integracaoOptions.classList.toggle('hidden', e.target.value !== 's');
        });
    });

    // Preencher selects de data
    const daySelect = document.getElementById('day');
    const monthSelect = document.getElementById('month');
    const yearSelect = document.getElementById('year');
    
    const today = new Date();
    if (daySelect && monthSelect && yearSelect) {
        for (let i = 1; i <= 31; i++) {
            const option = document.createElement('option');
            option.value = i.toString().padStart(2, '0');
            option.textContent = i.toString().padStart(2, '0');
            daySelect.appendChild(option);
        }
        for (let i = 1; i <= 12; i++) {
            const option = document.createElement('option');
            option.value = i.toString().padStart(2, '0');
            option.textContent = i.toString().padStart(2, '0');
            monthSelect.appendChild(option);
        }
        for (let i = today.getFullYear() - 2; i <= today.getFullYear() + 5; i++) {
            const option = document.createElement('option');
            option.value = i;
            option.textContent = i;
            yearSelect.appendChild(option);
        }
        daySelect.value = today.getDate().toString().padStart(2, '0');
        monthSelect.value = (today.getMonth() + 1).toString().padStart(2, '0');
        yearSelect.value = today.getFullYear();
    }

    // Evento de submit do formulário
    projectForm.addEventListener('submit', function(event) {
        event.preventDefault();

        startButton.disabled = true;
        startButton.textContent = 'Processando...';
        statusLabel.textContent = 'Enviando dados para o servidor...';
        statusLabel.style.color = 'var(--label-color)';

        const formData = new FormData(projectForm);
        
        // Adiciona a data formatada ao FormData
        if (daySelect && monthSelect && yearSelect) {
            const startDate = `${daySelect.value}-${monthSelect.value}-${yearSelect.value}`;
            formData.append('start_date', startDate);
        }

        fetch('/api/criar-projeto', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.message || 'Erro desconhecido no servidor') });
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                statusLabel.textContent = data.message;
                statusLabel.style.color = 'var(--success-color)';
                projectForm.reset();
                // Reseta o botão de DEIP
                if (deipFilename) deipFilename.textContent = '';
                if (deipButton) {
                    deipButton.style.backgroundColor = 'var(--primary-color)';
                    deipButton.textContent = 'Selecionar DEIP (.pdf)...';
                }
                // Reseta data para hoje
                if (daySelect && monthSelect && yearSelect) {
                    daySelect.value = today.getDate().toString().padStart(2, '0');
                    monthSelect.value = (today.getMonth() + 1).toString().padStart(2, '0');
                    yearSelect.value = today.getFullYear();
                }
            } else {
                statusLabel.textContent = `Erro: ${data.message}`;
                statusLabel.style.color = 'var(--error-color)';
            }
        })
        .catch(error => {
            console.error('Erro no fetch:', error);
            statusLabel.textContent = `Erro crítico: ${error.message}`;
            statusLabel.style.color = 'var(--error-color)';
        })
        .finally(() => {
            startButton.disabled = false;
            startButton.textContent = 'Iniciar Automação Completa';
        });
    });
});
