/**
 * Chart.js helper wrappers with modern design themes and mobile responsiveness
 */

const chartInstances = {};

function destroyChartIfExists(chartId) {
  if (chartInstances[chartId]) {
    chartInstances[chartId].destroy();
    delete chartInstances[chartId];
  }
}

// 1. Monthly Income vs Expenses Bar Chart
function renderMonthlyBarChart(canvasId, monthlyData) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  destroyChartIfExists(canvasId);

  const labels = monthlyData.map(d => d.month_label);
  const incomeVals = monthlyData.map(d => d.income);
  const expenseVals = monthlyData.map(d => d.expense);

  chartInstances[canvasId] = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Income',
          data: incomeVals,
          backgroundColor: '#10b981',
          borderRadius: 6,
          barPercentage: 0.6,
          categoryPercentage: 0.7,
        },
        {
          label: 'Expenses',
          data: expenseVals,
          backgroundColor: '#ef4444',
          borderRadius: 6,
          barPercentage: 0.6,
          categoryPercentage: 0.7,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: {
            boxWidth: 12,
            font: { family: 'Inter', size: 12, weight: '500' }
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `${context.dataset.label}: ₹${context.raw.toLocaleString('en-IN')}`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { font: { family: 'Inter', size: 11 } }
        },
        y: {
          grid: { color: '#f1f5f9' },
          ticks: {
            font: { family: 'Inter', size: 11 },
            callback: function(val) {
              return '₹' + (val >= 1000 ? (val / 1000).toFixed(0) + 'k' : val);
            }
          }
        }
      }
    }
  });
}

// 2. Category Breakdown Doughnut Chart
function renderCategoryDoughnutChart(canvasId, categories) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  destroyChartIfExists(canvasId);

  if (!categories || categories.length === 0) {
    return;
  }

  const labels = categories.map(c => c.category_name);
  const data = categories.map(c => c.total_amount);
  const colors = categories.map(c => c.color || '#4f46e5');

  chartInstances[canvasId] = new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: colors,
        borderWidth: 2,
        borderColor: '#ffffff',
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '70%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            boxWidth: 10,
            font: { family: 'Inter', size: 11 }
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const val = context.raw;
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
              return `${context.label}: ₹${val.toLocaleString('en-IN')} (${pct}%)`;
            }
          }
        }
      }
    }
  });
}

// 3. Daily Spending Trend Line Chart
function renderTrendLineChart(canvasId, labels, values) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  destroyChartIfExists(canvasId);

  const ctx = canvas.getContext('2d');
  const gradient = ctx.createLinearGradient(0, 0, 0, 300);
  gradient.addColorStop(0, 'rgba(79, 70, 229, 0.25)');
  gradient.addColorStop(1, 'rgba(79, 70, 229, 0.00)');

  chartInstances[canvasId] = new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Daily Spending',
        data: values,
        borderColor: '#4f46e5',
        backgroundColor: gradient,
        borderWidth: 2.5,
        fill: true,
        tension: 0.35,
        pointRadius: 2,
        pointHoverRadius: 6,
        pointBackgroundColor: '#4f46e5',
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `Spent: ₹${context.raw.toLocaleString('en-IN')}`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            maxTicksLimit: 12,
            font: { family: 'Inter', size: 11 }
          }
        },
        y: {
          grid: { color: '#f1f5f9' },
          ticks: {
            font: { family: 'Inter', size: 11 },
            callback: function(val) {
              return '₹' + (val >= 1000 ? (val / 1000).toFixed(0) + 'k' : val);
            }
          }
        }
      }
    }
  });
}
