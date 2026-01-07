document.addEventListener('DOMContentLoaded', function() {
    const fieldsets = document.querySelectorAll('fieldset');
    if (fieldsets.length === 0) return;

    // Crea il contenitore dei tab
    const tabContainer = document.createElement('div');
    tabContainer.className = 'admin-tabs-nav';
    fieldsets[0].parentNode.insertBefore(tabContainer, fieldsets[0]);

    fieldsets.forEach((fieldset, index) => {
        const title = fieldset.querySelector('h2').innerText;
        
        // Crea il bottone del tab
        const tabBtn = document.createElement('button');
        tabBtn.innerText = title;
        tabBtn.type = 'button';
        tabBtn.className = 'tab-btn' + (index === 0 ? ' active' : '');
        
        tabBtn.onclick = () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            tabBtn.classList.add('active');
            fieldsets.forEach(f => f.style.display = 'none');
            fieldset.style.display = 'block';
        };

        tabContainer.appendChild(tabBtn);
        if (index > 0) fieldset.style.display = 'none';
        
        // Nasconde l'header originale del fieldset
        fieldset.querySelector('h2').style.display = 'none';
    });
});