async function loadSummary() {
  const response = await fetch('/api/summary');
  const data = await response.json();

  const container = document.getElementById('summaryCards');
  const cards = [
    ['Total Cases', data.total_cases],
    ['Risk Score', data.risk_score],
    ['Status', data.status],
    ['Critical', data.critical_cases],
  ];

  container.innerHTML = cards
    .map(
      ([label, value]) => `
        <div class="metric">
          <span class="label">${label}</span>
          <span class="value">${value}</span>
        </div>
      `
    )
    .join('');
}

async function submitAssessment(event) {
  event.preventDefault();

  const form = event.currentTarget;
  const formData = Object.fromEntries(new FormData(form).entries());

  const response = await fetch('/api/assess', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...formData,
      amount: Number(formData.amount),
      history: Number(formData.history),
      alerts: Number(formData.alerts),
    }),
  });

  const result = await response.json();
  const box = document.getElementById('assessmentResult');

  box.classList.remove('hidden');
  box.innerHTML = `
    <h3>Assessment Result</h3>
    <p><strong>Account:</strong> ${result.account_id}</p>
    <p><strong>Risk Score:</strong> ${result.score}</p>
    <p><strong>Risk Level:</strong> ${result.risk_level}</p>
    <p><strong>Recommendation:</strong> ${result.recommendation}</p>
  `;
}

document.getElementById('refreshBtn').addEventListener('click', loadSummary);
document.getElementById('riskForm').addEventListener('submit', submitAssessment);
loadSummary();
