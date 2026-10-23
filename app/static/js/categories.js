/**
 * Categories Controller
 */

document.addEventListener('DOMContentLoaded', () => {
  const newCatForm = document.getElementById('newCategoryForm');
  const newCatName = document.getElementById('newCatName');
  const newCatIcon = document.getElementById('newCatIcon');
  const newCatColor = document.getElementById('newCatColor');
  const newCatError = document.getElementById('newCatError');
  const saveCategoryBtn = document.getElementById('saveCategoryBtn');
  const newCategoryModalEl = document.getElementById('newCategoryModal');

  // Attach delete buttons
  function attachCategoryDeleteListeners() {
    document.querySelectorAll('.delete-cat-btn').forEach(btn => {
      btn.onclick = async () => {
        const id = btn.getAttribute('data-id');
        const name = btn.getAttribute('data-name');

        if (confirm(`Are you sure you want to delete the category "${name}"?`)) {
          try {
            const res = await fetch(`/api/categories/${id}`, { method: 'DELETE' });
            const data = await res.json();
            if (res.ok && data.success) {
              const card = document.getElementById(`cat-card-${id}`);
              if (card) card.remove();
            } else {
              alert(data.error || 'Failed to delete category.');
            }
          } catch (e) {
            alert('Network error while deleting category.');
          }
        }
      };
    });
  }

  attachCategoryDeleteListeners();

  // Create Custom Category Handler
  if (newCatForm) {
    newCatForm.onsubmit = async (e) => {
      e.preventDefault();
      newCatError.classList.add('d-none');
      saveCategoryBtn.disabled = true;

      const type = document.querySelector('input[name="new_cat_type"]:checked').value;
      const name = newCatName.value.trim();
      const icon = newCatIcon.value;
      const color = newCatColor.value;

      if (!name) {
        newCatError.textContent = 'Please enter a category name.';
        newCatError.classList.remove('d-none');
        saveCategoryBtn.disabled = false;
        return;
      }

      try {
        const res = await fetch('/api/categories', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, type, icon, color })
        });

        const data = await res.json();
        if (res.ok && data.success) {
          window.location.reload();
        } else {
          newCatError.textContent = data.error || 'Failed to create category.';
          newCatError.classList.remove('d-none');
        }
      } catch (err) {
        newCatError.textContent = 'Network error while creating category.';
        newCatError.classList.remove('d-none');
      } finally {
        saveCategoryBtn.disabled = false;
      }
    };
  }
});
