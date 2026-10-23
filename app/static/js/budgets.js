/**
 * Budgets & Goals Controller
 */

document.addEventListener('DOMContentLoaded', () => {
  const monthSelect = document.getElementById('budgetMonthSelect');
  const yearSelect = document.getElementById('budgetYearSelect');

  const overallCard = document.getElementById('overallBudgetCardContainer');
  const overallBadge = document.getElementById('overallBudgetBadge');
  const overallSpentText = document.getElementById('overallBudgetSpentText');
  const overallLimitText = document.getElementById('overallBudgetLimitText');
  const overallRemainingText = document.getElementById('overallBudgetRemainingText');
  const overallProgressBar = document.getElementById('overallProgressBar');

  const categoryBudgetsGrid = document.getElementById('categoryBudgetsGrid');

  const setBudgetModalEl = document.getElementById('setBudgetModal');
  const setBudgetForm = document.getElementById('setBudgetForm');
  const budgetCatSelect = document.getElementById('budgetCategorySelect');
  const budgetAmountInput = document.getElementById('budgetAmountInput');
  const setBudgetError = document.getElementById('setBudgetError');
  const saveBudgetBtn = document.getElementById('saveBudgetBtn');

  // Set initial month & year to current
  const now = new Date();
  if (monthSelect) monthSelect.value = now.getMonth() + 1;
  if (yearSelect) yearSelect.value = now.getFullYear();

  // Load Budgets Data
  async function loadBudgets() {
    const month = monthSelect.value;
    const year = yearSelect.value;

    try {
      const res = await fetch(`/api/budgets?month=${month}&year=${year}`);
      if (!res.ok) throw new Error('Failed to fetch budgets');
      const data = await res.json();

      renderOverallBudget(data.overall_budget, data.total_spent);
      renderCategoryBudgets(data.category_budgets);
    } catch (err) {
      console.error('Budgets load error:', err);
      categoryBudgetsGrid.innerHTML = `
        <div class="col-12 text-center py-5 text-danger">Error loading budgets.</div>
      `;
    }
  }

  // Render Overall Budget Card
  function renderOverallBudget(overall, totalSpent) {
    if (!overall) {
      overallBadge.innerHTML = `<span class="badge bg-light text-muted">No limit set</span>`;
      overallSpentText.textContent = `Spent: ${formatCurrency(totalSpent)}`;
      overallLimitText.textContent = `Limit: Not Set`;
      overallRemainingText.textContent = `N/A`;
      overallRemainingText.className = 'fs-4 fw-bold text-muted';
      overallProgressBar.style.width = '0%';
      overallProgressBar.className = 'progress-bar bg-secondary';
      return;
    }

    const colorClass = overall.status === 'danger' ? 'bg-danger' : (overall.status === 'warning' ? 'bg-warning' : 'bg-primary');
    const badgeClass = overall.status === 'danger' ? 'bg-danger-subtle text-danger' : (overall.status === 'warning' ? 'bg-warning-subtle text-warning' : 'bg-primary-subtle text-primary');

    overallBadge.innerHTML = `<span class="badge ${badgeClass}">${overall.status_text} (${overall.utilization}%)</span>`;
    overallSpentText.textContent = `Spent: ${formatCurrency(overall.spent)}`;
    overallLimitText.textContent = `Limit: ${formatCurrency(overall.limit)}`;

    overallRemainingText.textContent = formatCurrency(overall.remaining);
    if (overall.remaining < 0) {
      overallRemainingText.className = 'fs-4 fw-bold text-danger';
    } else {
      overallRemainingText.className = 'fs-4 fw-bold text-success';
    }

    overallProgressBar.style.width = `${Math.min(100, overall.utilization)}%`;
    overallProgressBar.className = `progress-bar ${colorClass}`;
  }

  // Render Category Budgets Grid
  function renderCategoryBudgets(budgets) {
    categoryBudgetsGrid.innerHTML = '';

    if (!budgets || budgets.length === 0) {
      categoryBudgetsGrid.innerHTML = `
        <div class="col-12 text-center py-5 text-muted small">
          No category budgets set for this month.<br>
          Click <strong>Set Limit</strong> above to create one.
        </div>
      `;
      return;
    }

    budgets.forEach(b => {
      const colorClass = b.status === 'danger' ? 'bg-danger' : (b.status === 'warning' ? 'bg-warning' : 'bg-success');
      const badgeClass = b.status === 'danger' ? 'bg-danger-subtle text-danger' : (b.status === 'warning' ? 'bg-warning-subtle text-warning' : 'bg-success-subtle text-success');

      const col = document.createElement('div');
      col.className = 'col-12 col-md-6 col-lg-4';
      col.innerHTML = `
        <div class="card card-modern p-3 h-100 border-0 shadow-sm">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <div class="d-flex align-items-center gap-2">
              <div class="rounded-circle text-white d-flex align-items-center justify-content-center" style="width: 36px; height: 36px; background-color: ${b.category_color};">
                <i class="bi ${b.category_icon} small"></i>
              </div>
              <div>
                <h6 class="fw-bold mb-0 text-dark">${b.category_name}</h6>
                <span class="badge ${badgeClass}" style="font-size: 0.7rem;">${b.status_text}</span>
              </div>
            </div>
            <button class="btn btn-sm btn-light border-0 delete-budget-btn text-muted" data-id="${b.id}" title="Delete Budget">
              <i class="bi bi-x-lg"></i>
            </button>
          </div>

          <div class="my-2">
            <div class="d-flex justify-content-between small text-muted mb-1">
              <span>${b.utilization}% spent</span>
              <span>Remaining: <strong>${formatCurrency(b.remaining)}</strong></span>
            </div>
            <div class="progress" style="height: 8px;">
              <div class="progress-bar ${colorClass}" role="progressbar" style="width: ${Math.min(100, b.utilization)}%"></div>
            </div>
          </div>

          <div class="d-flex justify-content-between text-muted small pt-2 border-top mt-auto" style="font-size: 0.78rem;">
            <span>Spent: ${formatCurrency(b.spent)}</span>
            <span>Limit: ${formatCurrency(b.limit)}</span>
          </div>
        </div>
      `;
      categoryBudgetsGrid.appendChild(col);
    });

    // Attach delete listeners
    document.querySelectorAll('.delete-budget-btn').forEach(btn => {
      btn.onclick = async () => {
        const id = btn.getAttribute('data-id');
        if (confirm('Delete this category budget limit?')) {
          try {
            const res = await fetch(`/api/budgets/${id}`, { method: 'DELETE' });
            if (res.ok) {
              loadBudgets();
            }
          } catch (e) {
            alert('Failed to delete budget.');
          }
        }
      };
    });
  }

  // Save Budget Form Handler
  if (setBudgetForm) {
    setBudgetForm.onsubmit = async (e) => {
      e.preventDefault();
      setBudgetError.classList.add('d-none');
      saveBudgetBtn.disabled = true;

      const category_id = budgetCatSelect.value ? parseInt(budgetCatSelect.value) : null;
      const month = parseInt(monthSelect.value);
      const year = parseInt(yearSelect.value);
      const amount = parseFloat(budgetAmountInput.value);

      if (!amount || amount <= 0) {
        setBudgetError.textContent = 'Please enter an amount greater than zero.';
        setBudgetError.classList.remove('d-none');
        saveBudgetBtn.disabled = false;
        return;
      }

      try {
        const res = await fetch('/api/budgets', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            category_id,
            month,
            year,
            amount
          })
        });

        const data = await res.json();
        if (res.ok && data.success) {
          setBudgetForm.reset();
          const modalInstance = bootstrap.Modal.getInstance(setBudgetModalEl);
          if (modalInstance) modalInstance.hide();
          loadBudgets();
        } else {
          setBudgetError.textContent = (data.errors || [data.error || 'Failed to save budget']).join(' ');
          setBudgetError.classList.remove('d-none');
        }
      } catch (err) {
        setBudgetError.textContent = 'Network error while saving budget.';
        setBudgetError.classList.remove('d-none');
      } finally {
        saveBudgetBtn.disabled = false;
      }
    };
  }

  // Event Listeners
  if (monthSelect) monthSelect.addEventListener('change', loadBudgets);
  if (yearSelect) yearSelect.addEventListener('change', loadBudgets);

  // Initial Load
  loadBudgets();
});
