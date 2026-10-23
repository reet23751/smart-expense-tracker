/**
 * Spending Analytics Controller
 */

document.addEventListener('DOMContentLoaded', () => {
  const periodSelect = document.getElementById('analyticsPeriodSelect');
  const expenseList = document.getElementById('analyticsExpenseList');
  const incomeList = document.getElementById('analyticsIncomeList');

  async function loadAnalytics() {
    const period = periodSelect.value;
    try {
      const res = await fetch(`/api/analytics?period=${period}`);
      if (!res.ok) throw new Error('Failed to fetch analytics');
      const data = await res.json();

      // 1. Daily Spending Trend Line Chart
      if (data.trends) {
        renderTrendLineChart('spendingTrendChart', data.trends.labels, data.trends.values);
      }

      // 2. Expense Doughnut Chart & List
      if (data.expense_categories) {
        renderCategoryDoughnutChart('analyticsExpenseDoughnut', data.expense_categories.categories);
        renderCategoryAllocationList(expenseList, data.expense_categories.categories);
      }

      // 3. Income Doughnut Chart & List
      if (data.income_categories) {
        renderCategoryDoughnutChart('analyticsIncomeDoughnut', data.income_categories.categories);
        renderCategoryAllocationList(incomeList, data.income_categories.categories);
      }

      // 4. Monthly 6-Month Bar Chart
      if (data.monthly_comparison) {
        renderMonthlyBarChart('analyticsMonthlyBar', data.monthly_comparison);
      }

    } catch (err) {
      console.error('Analytics load error:', err);
    }
  }

  function renderCategoryAllocationList(container, categories) {
    if (!container) return;
    container.innerHTML = '';

    if (!categories || categories.length === 0) {
      container.innerHTML = `<div class="text-center py-3 text-muted small">No data recorded for this period.</div>`;
      return;
    }

    categories.forEach(c => {
      const item = document.createElement('div');
      item.className = 'd-flex justify-content-between align-items-center mb-2 small';
      item.innerHTML = `
        <div class="d-flex align-items-center gap-2">
          <div class="rounded-circle" style="width: 10px; height: 10px; background-color: ${c.color || '#4f46e5'};"></div>
          <span class="text-dark fw-medium">${c.category_name}</span>
        </div>
        <div>
          <span class="fw-bold">${formatCurrency(c.total_amount)}</span>
          <span class="text-muted ms-1" style="font-size: 0.75rem;">(${c.percentage}%)</span>
        </div>
      `;
      container.appendChild(item);
    });
  }

  if (periodSelect) {
    periodSelect.addEventListener('change', loadAnalytics);
  }

  // Initial load
  loadAnalytics();
});
