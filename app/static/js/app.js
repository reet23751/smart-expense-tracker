/**
 * Smart Expense Tracker & AI Advisor
 * Core Application JavaScript
 */

// Helper to format currency in Indian Rupees (₹)
function formatCurrency(amount) {
  const num = parseFloat(amount || 0);
  return '₹' + num.toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

// Global cached categories list
let globalCategories = [];

// Fetch categories from API
async function loadCategories(type = null) {
  try {
    const url = type ? `/api/categories?type=${type}` : '/api/categories';
    const res = await fetch(url);
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.error('Failed to load categories:', err);
  }
  return [];
}

// Populate a select element with category options
function populateCategorySelect(selectEl, categories, selectedId = null) {
  if (!selectEl) return;
  selectEl.innerHTML = '<option value="" disabled selected>Select category...</option>';
  categories.forEach(cat => {
    const opt = document.createElement('option');
    opt.value = cat.id;
    opt.textContent = cat.name;
    if (selectedId && cat.id === parseInt(selectedId)) {
      opt.selected = true;
    }
    selectEl.appendChild(opt);
  });
}

// Initialize Universal Quick Add Modal
document.addEventListener('DOMContentLoaded', async () => {
  const quickAddModalEl = document.getElementById('quickAddModal');
  const quickAddForm = document.getElementById('quickAddForm');
  const modalCategory = document.getElementById('modalCategory');
  const modalDate = document.getElementById('modalDate');
  const modalTypeExpense = document.getElementById('modalTypeExpense');
  const modalTypeIncome = document.getElementById('modalTypeIncome');
  const modalError = document.getElementById('modalFormError');
  const modalSaveBtn = document.getElementById('modalSaveBtn');
  const modalSaveSpinner = document.getElementById('modalSaveSpinner');

  // Set default date to today
  if (modalDate) {
    const today = new Date().toISOString().split('T')[0];
    modalDate.value = today;
  }

  // Preload categories
  globalCategories = await loadCategories();

  // Function to refresh category choices in quick add
  const updateModalCategories = (type) => {
    const filtered = globalCategories.filter(c => c.type === type);
    populateCategorySelect(modalCategory, filtered);
  };

  if (modalTypeExpense && modalTypeIncome) {
    updateModalCategories('expense');
    modalTypeExpense.addEventListener('change', () => updateModalCategories('expense'));
    modalTypeIncome.addEventListener('change', () => updateModalCategories('income'));
  }

  // Quick Add Form Submit
  if (quickAddForm) {
    quickAddForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      modalError.classList.add('d-none');
      modalError.textContent = '';

      const type = document.querySelector('input[name="modal_type"]:checked').value;
      const amount = parseFloat(document.getElementById('modalAmount').value);
      const categoryId = parseInt(modalCategory.value);
      const txDate = modalDate.value;
      const description = document.getElementById('modalDescription').value.trim();

      if (!amount || amount <= 0) {
        modalError.textContent = 'Please enter a valid amount greater than zero.';
        modalError.classList.remove('d-none');
        return;
      }

      if (!categoryId) {
        modalError.textContent = 'Please select a category.';
        modalError.classList.remove('d-none');
        return;
      }

      modalSaveBtn.disabled = true;
      modalSaveSpinner.classList.remove('d-none');

      try {
        const response = await fetch('/api/transactions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type,
            amount,
            category_id: categoryId,
            transaction_date: txDate,
            description
          })
        });

        const result = await response.json();

        if (response.ok && result.success) {
          // Reset form
          quickAddForm.reset();
          if (modalDate) modalDate.value = new Date().toISOString().split('T')[0];
          if (modalTypeExpense) modalTypeExpense.checked = true;
          updateModalCategories('expense');

          // Close modal
          const modalInstance = bootstrap.Modal.getInstance(quickAddModalEl);
          if (modalInstance) modalInstance.hide();

          // Dispatch event to refresh current view
          window.dispatchEvent(new CustomEvent('transactionUpdated', { detail: result.transaction }));
        } else {
          modalError.textContent = (result.errors || [result.error || 'Failed to save transaction']).join(' ');
          modalError.classList.remove('d-none');
        }
      } catch (err) {
        modalError.textContent = 'Network error while saving transaction. Please try again.';
        modalError.classList.remove('d-none');
      } finally {
        modalSaveBtn.disabled = false;
        modalSaveSpinner.classList.add('d-none');
      }
    });
  }
});
