/**
 * Reports & CSV Export Controller
 */

document.addEventListener('DOMContentLoaded', () => {
  const periodSelect = document.getElementById('reportPeriodSelect');
  const exportBtn = document.getElementById('exportCsvBtn');
  const historyTableBody = document.getElementById('reportHistoryTableBody');
  const catTableBody = document.getElementById('reportCategoryTableBody');
  const dateRangeLabel = document.getElementById('reportDateRangeLabel');

  async function loadReports() {
    const period = periodSelect.value;
    try {
      const res = await fetch(`/api/reports/monthly?period=${period}`);
      if (!res.ok) throw new Error('Failed to load reports');
      const data = await res.json();

      if (dateRangeLabel && data.period) {
        dateRangeLabel.textContent = `Period: ${data.period.start_date} to ${data.period.end_date}`;
      }

      // 1. Render 12-Month Performance History Table
      renderHistoryTable(data.monthly_history);

      // 2. Render Category Totals Table
      renderCategoryTable(data.expense_breakdown);

      // 3. Update CSV export link with current period parameters
      if (exportBtn && data.period) {
        exportBtn.href = `/api/reports/export-csv?start_date=${data.period.start_date}&end_date=${data.period.end_date}`;
      }

    } catch (err) {
      console.error('Reports load error:', err);
    }
  }

  function renderHistoryTable(history) {
    if (!historyTableBody) return;
    historyTableBody.innerHTML = '';

    if (!history || history.length === 0) {
      historyTableBody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-muted">No historical statements available.</td></tr>`;
      return;
    }

    history.forEach(row => {
      const isPositive = row.net_savings >= 0;
      const statusBadge = isPositive ? '<span class="badge bg-success-subtle text-success">Surplus</span>' : '<span class="badge bg-danger-subtle text-danger">Deficit</span>';
      const savingsClass = isPositive ? 'text-success fw-bold' : 'text-danger fw-bold';

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="ps-4 fw-medium text-dark">${row.month_label}</td>
        <td class="text-end text-success">${formatCurrency(row.income)}</td>
        <td class="text-end text-danger">${formatCurrency(row.expense)}</td>
        <td class="text-end ${savingsClass}">${formatCurrency(row.net_savings)}</td>
        <td class="text-end pe-4">${statusBadge}</td>
      `;
      historyTableBody.appendChild(tr);
    });
  }

  function renderCategoryTable(breakdown) {
    if (!catTableBody) return;
    catTableBody.innerHTML = '';

    const categories = (breakdown && breakdown.categories) || [];
    if (categories.length === 0) {
      catTableBody.innerHTML = `<tr><td colspan="4" class="text-center py-4 text-muted">No expense records found for this period.</td></tr>`;
      return;
    }

    categories.forEach(cat => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="ps-4">
          <div class="d-flex align-items-center gap-2">
            <div class="rounded-circle text-white d-flex align-items-center justify-content-center" style="width: 28px; height: 28px; background-color: ${cat.color || '#6c757d'};">
              <i class="bi ${cat.icon || 'bi-tag'} small"></i>
            </div>
            <span class="fw-medium text-dark">${cat.category_name}</span>
          </div>
        </td>
        <td class="text-center text-muted small">${cat.item_count} transactions</td>
        <td class="text-end fw-bold text-dark">${formatCurrency(cat.total_amount)}</td>
        <td class="text-end pe-4">
          <div class="d-inline-flex align-items-center gap-2">
            <div class="progress" style="width: 60px; height: 6px;">
              <div class="progress-bar" style="width: ${cat.percentage}%; background-color: ${cat.color || '#4f46e5'};"></div>
            </div>
            <span class="small fw-semibold text-muted" style="min-width: 40px;">${cat.percentage}%</span>
          </div>
        </td>
      `;
      catTableBody.appendChild(tr);
    });
  }

  if (periodSelect) {
    periodSelect.addEventListener('change', loadReports);
  }

  // Initial load
  loadReports();
});
