/**
 * Transactions Management Controller
 */

document.addEventListener('DOMContentLoaded', () => {
  let currentPage = 1;
  const perPage = 15;

  const searchInput = document.getElementById('txSearchInput');
  const typeFilter = document.getElementById('txTypeFilter');
  const categoryFilter = document.getElementById('txCategoryFilter');
  const sortFilter = document.getElementById('txSortFilter');
  const resetFiltersBtn = document.getElementById('txResetFiltersBtn');

  const tableBody = document.getElementById('txTableBody');
  const mobileCardsContainer = document.getElementById('txMobileCardsContainer');
  const paginationSummary = document.getElementById('txPaginationSummary');
  const prevPageBtn = document.getElementById('txPrevPageBtn');
  const nextPageBtn = document.getElementById('txNextPageBtn');

  // Edit Modal elements
  const editModalEl = document.getElementById('editTxModal');
  const editForm = document.getElementById('editTxForm');
  const editId = document.getElementById('editTxId');
  const editAmount = document.getElementById('editTxAmount');
  const editCategory = document.getElementById('editTxCategory');
  const editDate = document.getElementById('editTxDate');
  const editDescription = document.getElementById('editTxDescription');
  const editTypeExpense = document.getElementById('editTypeExpense');
  const editTypeIncome = document.getElementById('editTypeIncome');
  const editError = document.getElementById('editTxError');
  const editSaveBtn = document.getElementById('editTxSaveBtn');

  // Delete Modal elements
  const deleteModalEl = document.getElementById('deleteTxModal');
  const deleteIdInput = document.getElementById('deleteTxId');
  const confirmDeleteBtn = document.getElementById('confirmDeleteTxBtn');

  // Fetch and Render Transactions
  async function fetchTransactions() {
    const search = searchInput ? searchInput.value.trim() : '';
    const type = typeFilter ? typeFilter.value : 'all';
    const categoryId = categoryFilter ? categoryFilter.value : '';
    const sortVal = sortFilter ? sortFilter.value : 'date-desc';

    const [sortBy, sortOrder] = sortVal.split('-');

    let url = `/api/transactions?page=${currentPage}&per_page=${perPage}&type=${type}&sort_by=${sortBy}&sort_order=${sortOrder}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (categoryId) url += `&category_id=${categoryId}`;

    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch transactions');
      const data = await res.json();

      renderDesktopTable(data.transactions);
      renderMobileCards(data.transactions);
      updatePagination(data);
    } catch (err) {
      console.error('Fetch transactions error:', err);
      tableBody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-danger">Error loading transactions.</td></tr>`;
      mobileCardsContainer.innerHTML = `<div class="text-center py-4 text-danger">Error loading transactions.</div>`;
    }
  }

  // Render Desktop Table
  function renderDesktopTable(transactions) {
    if (!tableBody) return;
    tableBody.innerHTML = '';

    if (!transactions || transactions.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="6" class="text-center py-5 text-muted">No transactions found matching your criteria.</td></tr>`;
      return;
    }

    transactions.forEach(tx => {
      const isIncome = tx.type === 'income';
      const sign = isIncome ? '+' : '-';
      const amountClass = isIncome ? 'text-success fw-bold' : 'text-danger fw-bold';
      const badgeClass = isIncome ? 'badge-income' : 'badge-expense';

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="ps-4 text-muted small">${tx.transaction_date}</td>
        <td>
          <div class="d-flex align-items-center gap-2">
            <div class="rounded-circle text-white d-flex align-items-center justify-content-center" style="width: 32px; height: 32px; background-color: ${tx.category_color};">
              <i class="bi ${tx.category_icon} small"></i>
            </div>
            <span class="fw-semibold text-dark">${tx.category_name}</span>
          </div>
        </td>
        <td class="text-secondary">${tx.description || '<span class="text-muted fst-italic">No note</span>'}</td>
        <td><span class="${badgeClass}">${tx.type.toUpperCase()}</span></td>
        <td class="text-end ${amountClass}">${sign}${formatCurrency(tx.amount)}</td>
        <td class="text-end pe-4">
          <button class="btn btn-sm btn-light border edit-btn me-1" data-id="${tx.id}" title="Edit Transaction">
            <i class="bi bi-pencil"></i>
          </button>
          <button class="btn btn-sm btn-light border text-danger delete-btn" data-id="${tx.id}" title="Delete Transaction">
            <i class="bi bi-trash3"></i>
          </button>
        </td>
      `;
      tableBody.appendChild(tr);
    });

    attachActionListeners();
  }

  // Render Mobile Touch Cards
  function renderMobileCards(transactions) {
    if (!mobileCardsContainer) return;
    mobileCardsContainer.innerHTML = '';

    if (!transactions || transactions.length === 0) {
      mobileCardsContainer.innerHTML = `<div class="text-center py-5 text-muted">No transactions found.</div>`;
      return;
    }

    transactions.forEach(tx => {
      const isIncome = tx.type === 'income';
      const sign = isIncome ? '+' : '-';
      const amountClass = isIncome ? 'text-success' : 'text-danger';

      const card = document.createElement('div');
      card.className = 'transaction-card';
      card.innerHTML = `
        <div class="d-flex align-items-center gap-3">
          <div class="tx-cat-icon text-white" style="background-color: ${tx.category_color};">
            <i class="bi ${tx.category_icon}"></i>
          </div>
          <div>
            <div class="fw-semibold text-dark small">${tx.category_name}</div>
            <div class="text-muted" style="font-size: 0.75rem;">
              ${tx.description ? tx.description + ' &bull; ' : ''}${tx.transaction_date}
            </div>
          </div>
        </div>
        <div class="d-flex align-items-center gap-2">
          <div class="text-end">
            <div class="fw-bold ${amountClass}">${sign}${formatCurrency(tx.amount)}</div>
          </div>
          <div class="dropdown">
            <button class="btn btn-sm btn-light border-0" type="button" data-bs-toggle="dropdown">
              <i class="bi bi-three-dots-vertical"></i>
            </button>
            <ul class="dropdown-menu dropdown-menu-end shadow-sm border-0">
              <li><a class="dropdown-item edit-btn" href="#" data-id="${tx.id}"><i class="bi bi-pencil me-2 text-primary"></i>Edit</a></li>
              <li><a class="dropdown-item text-danger delete-btn" href="#" data-id="${tx.id}"><i class="bi bi-trash3 me-2"></i>Delete</a></li>
            </ul>
          </div>
        </div>
      `;
      mobileCardsContainer.appendChild(card);
    });

    attachActionListeners();
  }

  // Attach Edit and Delete listeners
  function attachActionListeners() {
    document.querySelectorAll('.edit-btn').forEach(btn => {
      btn.onclick = (e) => {
        e.preventDefault();
        const txId = btn.getAttribute('data-id');
        openEditModal(txId);
      };
    });

    document.querySelectorAll('.delete-btn').forEach(btn => {
      btn.onclick = (e) => {
        e.preventDefault();
        const txId = btn.getAttribute('data-id');
        openDeleteModal(txId);
      };
    });
  }

  // Update Pagination Controls
  function updatePagination(data) {
    if (!paginationSummary) return;
    const start = data.total === 0 ? 0 : (data.page - 1) * perPage + 1;
    const end = Math.min(data.page * perPage, data.total);
    paginationSummary.textContent = `Showing ${start} to ${end} of ${data.total} transactions`;

    prevPageBtn.disabled = !data.has_prev;
    nextPageBtn.disabled = !data.has_next;
  }

  // Open Edit Modal
  async function openEditModal(txId) {
    try {
      const res = await fetch(`/api/transactions/${txId}`);
      if (!res.ok) throw new Error('Failed to fetch transaction details');
      const tx = await res.json();

      editId.value = tx.id;
      editAmount.value = tx.amount;
      editDate.value = tx.transaction_date;
      editDescription.value = tx.description || '';

      if (tx.type === 'expense') {
        editTypeExpense.checked = true;
      } else {
        editTypeIncome.checked = true;
      }

      // Populate categories matching transaction type
      const updateEditCategories = (type) => {
        const filtered = globalCategories.filter(c => c.type === type);
        populateCategorySelect(editCategory, filtered, tx.category_id);
      };

      updateEditCategories(tx.type);
      editTypeExpense.onchange = () => updateEditCategories('expense');
      editTypeIncome.onchange = () => updateEditCategories('income');

      editError.classList.add('d-none');
      const modal = new bootstrap.Modal(editModalEl);
      modal.show();
    } catch (err) {
      alert('Could not load transaction details.');
    }
  }

  // Save Edit Form
  if (editForm) {
    editForm.onsubmit = async (e) => {
      e.preventDefault();
      editError.classList.add('d-none');
      editSaveBtn.disabled = true;

      const txId = editId.value;
      const type = document.querySelector('input[name="edit_type"]:checked').value;
      const amount = parseFloat(editAmount.value);
      const categoryId = parseInt(editCategory.value);
      const txDate = editDate.value;
      const description = editDescription.value.trim();

      try {
        const res = await fetch(`/api/transactions/${txId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type,
            amount,
            category_id: categoryId,
            transaction_date: txDate,
            description
          })
        });

        const data = await res.json();
        if (res.ok && data.success) {
          const modalInstance = bootstrap.Modal.getInstance(editModalEl);
          if (modalInstance) modalInstance.hide();
          fetchTransactions();
          window.dispatchEvent(new CustomEvent('transactionUpdated', { detail: data.transaction }));
        } else {
          editError.textContent = (data.errors || [data.error || 'Failed to update transaction']).join(' ');
          editError.classList.remove('d-none');
        }
      } catch (err) {
        editError.textContent = 'Network error while updating transaction.';
        editError.classList.remove('d-none');
      } finally {
        editSaveBtn.disabled = false;
      }
    };
  }

  // Open Delete Confirmation Modal
  function openDeleteModal(txId) {
    deleteIdInput.value = txId;
    const modal = new bootstrap.Modal(deleteModalEl);
    modal.show();
  }

  // Confirm Delete Handler
  if (confirmDeleteBtn) {
    confirmDeleteBtn.onclick = async () => {
      const txId = deleteIdInput.value;
      confirmDeleteBtn.disabled = true;

      try {
        const res = await fetch(`/api/transactions/${txId}`, { method: 'DELETE' });
        if (res.ok) {
          const modalInstance = bootstrap.Modal.getInstance(deleteModalEl);
          if (modalInstance) modalInstance.hide();
          fetchTransactions();
          window.dispatchEvent(new CustomEvent('transactionUpdated', { detail: { id: txId } }));
        } else {
          alert('Failed to delete transaction.');
        }
      } catch (err) {
        alert('Network error while deleting transaction.');
      } finally {
        confirmDeleteBtn.disabled = false;
      }
    };
  }

  // Event Listeners for search & filters
  let searchTimeout;
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        currentPage = 1;
        fetchTransactions();
      }, 350);
    });
  }

  if (typeFilter) {
    typeFilter.addEventListener('change', () => {
      currentPage = 1;
      fetchTransactions();
    });
  }

  if (categoryFilter) {
    categoryFilter.addEventListener('change', () => {
      currentPage = 1;
      fetchTransactions();
    });
  }

  if (sortFilter) {
    sortFilter.addEventListener('change', () => {
      currentPage = 1;
      fetchTransactions();
    });
  }

  if (resetFiltersBtn) {
    resetFiltersBtn.addEventListener('click', () => {
      searchInput.value = '';
      typeFilter.value = 'all';
      categoryFilter.value = '';
      sortFilter.value = 'date-desc';
      currentPage = 1;
      fetchTransactions();
    });
  }

  if (prevPageBtn) {
    prevPageBtn.addEventListener('click', () => {
      if (currentPage > 1) {
        currentPage--;
        fetchTransactions();
      }
    });
  }

  if (nextPageBtn) {
    nextPageBtn.addEventListener('click', () => {
      currentPage++;
      fetchTransactions();
    });
  }

  // Listen to external adds
  window.addEventListener('transactionUpdated', fetchTransactions);

  // Initial Load
  fetchTransactions();
});
