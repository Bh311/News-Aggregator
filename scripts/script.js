document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('dark-mode-toggle');
    toggleBtn.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        document.querySelectorAll('.article').forEach(el => el.classList.toggle('dark-mode'));
    });
});
