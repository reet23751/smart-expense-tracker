/**
 * Dashboard Controller
 */

document.addEventListener('DOMContentLoaded', () => {
  const periodSelect = document.getElementById('dashboardPeriodSelect');
  const refreshBtn = document.getElementById('refreshDashboardBtn');

  const cardIncome = document.getElementById('cardTotalIncome');
  const cardExpenses = document.getElementById('cardTotalExpenses');
  const cardBalance = document.getElementById('cardNetBalance');
  const cardSavings = document.getElementById('cardSavingsRate');

  const aiSummaryPreview = document.getElementById('aiSummaryPreview');
  const aiTopTipPreview = document.getElementById('aiTopTipPreview');

  const budgetList = document.getElementById('budgetProgressList');
  const recentTxList = document.getElementById('recentTransactionsList');
  const doughnutEmptyState = document.getElementById('doughnutEmptyState');

  // Load Dashboard Data
  async function loadDashboard() {
    const period = periodSelect.value;
    try {
      const res = await fetch(`/api/dashboard/summary?period=${period}`);
      if (!res.ok) throw new Error('Failed to fetch dashboard summary');
      const data = await res.json();

      // 1. Update Summary Cards
      const summary = data.summary;
      cardIncome.textContent = formatCurrency(summary.total_income);
      cardExpenses.textContent = formatCurrency(summary.total_expenses);
      cardBalance.textContent = formatCurrency(summary.remaining_balance);
      cardSavings.textContent = `${summary.savings_rate}%`;

      if (summary.remaining_balance < 0) {
        cardBalance.classList.remove('text-primary');
        cardBalance.classList.add('text-danger');
      } else {
        cardBalance.classList.remove('text-danger');
        cardBalance.classList.add('text-primary');
      }

      // 2. Update AI Insight Preview
      if (data.latest_insight) {
        aiSummaryPreview.textContent = data.latest_insight.summary;
        const tips = data.latest_insight.savings_tips;
        if (tips && tips.length > 0) {
          aiTopTipPreview.innerHTML = `<i class="bi bi-lightbulb-fill text-warning me-1"></i> ${tips[0]}`;
        } else {
          aiTopTipPreview.textContent = '';
        }
      } else {
        aiSummaryPreview.textContent = "Click on AI Advisor to generate personalized spending insights based on your transactions.";
        aiTopTipPreview.textContent = '';
      }

      // 3. Update Category Doughnut Chart
      const categories = data.categories || [];
      if (categories.length > 0) {
        doughnutEmptyState.classList.add('d-none');
        renderCategoryDoughnutChart('categoryDoughnutChart', categories);
      } else {
        doughnutEmptyState.classList.remove('d-none');
        destroyChartIfExists('categoryDoughnutChart');
      }

      // 4. Update 6-Month Comparison Bar Chart
      fetchAnalyticsHistory();

      // 5. Update Budgets Progress
      renderBudgets(data.budgets);

      // 6. Update Recent Transactions
      renderRecentTransactions(data.recent_transactions);

    } catch (err) {
      console.error('Dashboard load error:', err);
    }
  }

  // Fetch 6-month historical data for bar chart
  async function fetchAnalyticsHistory() {
    try {
      const res = await fetch('/api/analytics?period=this-year');
      if (res.ok) {
        const d = await res.json();
        if (d.monthly_comparison) {
          renderMonthlyBarChart('monthlyCompChart', d.monthly_comparison);
        }
      }
    } catch (err) {
      console.error('Analytics history load error:', err);
    }
  }

  // Render Budgets progress list
  function renderBudgets(budgetData) {
    if (!budgetList) return;
    budgetList.innerHTML = '';

    const allBudgets = [];
    if (budgetData && budgetData.overall_budget) {
      allBudgets.push(budgetData.overall_budget);
    }
    if (budgetData && budgetData.category_budgets) {
      allBudgets.push(...budgetData.category_budgets);
    }

    if (allBudgets.length === 0) {
      budgetList.innerHTML = `
        <div class="text-center py-4 text-muted small">
          No monthly budgets set for this month.<br>
          <a href="/budgets" class="btn btn-sm btn-outline-primary rounded-pill mt-2">Set a Budget</a>
        </div>
      `;
      return;
    }

    allBudgets.forEach(b => {
      const progressColor = b.status === 'danger' ? 'bg-danger' : (b.status === 'warning' ? 'bg-warning' : 'bg-success');
      const badgeClass = b.status === 'danger' ? 'bg-danger-subtle text-danger' : (b.status === 'warning' ? 'bg-warning-subtle text-warning' : 'bg-success-subtle text-success');

      const item = document.createElement('div');
      item.className = 'mb-3 pb-3 border-bottom';
      item.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-1">
          <div class="d-flex align-items-center gap-2">
            <i class="bi ${b.category_icon}" style="color: ${b.category_color};"></i>
            <span class="fw-semibold small">${b.category_name}</span>
          </div>
          <span class="badge ${badgeClass} small">${b.status_text} (${b.utilization}%)</span>
        </div>
        <div class="progress mb-1" style="height: 8px;">
          <div class="progress-bar ${progressColor}" role="progressbar" style="width: ${Math.min(100, b.utilization)}%"></div>
        </div>
        <div class="d-flex justify-content-between text-muted" style="font-size: 0.75rem;">
          <span>Spent: ${formatCurrency(b.spent)}</span>
          <span>Limit: ${formatCurrency(b.limit)}</span>
        </div>
      `;
      budgetList.appendChild(item);
    });
  }

  // Render Recent Transactions
  function renderRecentTransactions(transactions) {
    if (!recentTxList) return;
    recentTxList.innerHTML = '';

    if (!transactions || transactions.length === 0) {
      recentTxList.innerHTML = `
        <div class="text-center py-5 text-muted small">
          No transactions yet. Click <strong>Add Transaction</strong> to start tracking!
        </div>
      `;
      return;
    }

    transactions.forEach(tx => {
      const isIncome = tx.type === 'income';
      const sign = isIncome ? '+' : '-';
      const amountColor = isIncome ? 'text-success' : 'text-danger';
      const bgBadge = isIncome ? 'bg-success-subtle' : 'bg-danger-subtle';

      const card = document.createElement('div');
      card.className = 'transaction-card';
      card.innerHTML = `
        <div class="d-flex align-items-center gap-3">
          <div class="tx-cat-icon text-white" style="background-color: ${tx.category_color || '#6c757d'};">
            <i class="bi ${tx.category_icon || 'bi-tag'}"></i>
          </div>
          <div>
            <div class="fw-semibold text-dark small">${tx.category_name}</div>
            <div class="text-muted" style="font-size: 0.75rem;">
              ${tx.description ? tx.description + ' &bull; ' : ''}${tx.transaction_date}
            </div>
          </div>
        </div>
        <div class="text-end">
          <div class="fw-bold ${amountColor}">${sign}${formatCurrency(tx.amount)}</div>
          <span class="badge ${bgBadge} ${amountColor} small" style="font-size: 0.7rem;">${tx.type.toUpperCase()}</span>
        </div>
      `;
      recentTxList.appendChild(card);
    });
  }

  // Event Listeners
  if (periodSelect) {
    periodSelect.addEventListener('change', loadDashboard);
  }
  if (refreshBtn) {
    refreshBtn.addEventListener('click', loadDashboard);
  }

  // Listen to cross-component transaction updates
  window.addEventListener('transactionUpdated', loadDashboard);

  // Initial load
  loadDashboard();
});
