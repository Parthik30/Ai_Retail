const API = "http://127.0.0.1:5000/api";
let salesChart, priceChart;
let currentData = null;

// Load products
fetch(`${API}/products`)
  .then(res => res.json())
  .then(products => {
    const select = document.getElementById("productSelect");
    products.forEach(p => {
      const opt = document.createElement("option");
      opt.value = p;
      opt.textContent = p;
      select.appendChild(opt);
    });
    updateDashboard();
  });

function updateDashboard() {
  const product = document.getElementById("productSelect").value;

  fetch(`${API}/dashboard?product=${encodeURIComponent(product)}`)
    .then(res => res.json())
    .then(d => {
      currentData = d;

      document.getElementById("sales").innerText = d.sales;
      document.getElementById("stock").innerText = d.stock;
      document.getElementById("price").innerText = "₹" + d.base_price;
      document.getElementById("discount").innerText = d.discount + "%";
      document.getElementById("finalPrice").innerText = "₹" + d.final_price;
      document.getElementById("profit").innerText = "₹" + d.profit;
      document.getElementById("statusText").innerText = d.inventory_status;
      document.getElementById("reorderQty").innerText = d.reorder_qty;

      inventoryHealth(d);
      aiDiscountBadge(d.inventory_status);

      drawCharts(d.sales_trend, d.price_trend);
    });
}

// Pricing strategy explanation
function updateStrategyInfo() {
  const radios = document.getElementsByName('pricingStrategy');
  let selected = null;
  for (const r of radios) {
    if (r.checked) { selected = r.value; break; }
  }

  const info = document.getElementById('strategyInfo');
  if (!info) return;

  if (selected === 'target_margin') {
    info.innerHTML = '<b>Target Margin %</b>: Set the desired profit margin. The system computes a final selling price that meets this margin target.';
  } else if (selected === 'markup') {
    info.innerHTML = '<b>Markup %</b>: Apply a markup percentage on top of cost to determine the selling price.';
  } else if (selected === 'increase') {
    info.innerHTML = '<b>Increase by %</b>: Increase the current price by the selected percentage (useful for temporary price changes).';
  } else {
    info.innerHTML = '';
  }
}

// Initialize strategy info on page load
document.addEventListener('DOMContentLoaded', function() {
  updateStrategyInfo();
});

// Manual discount simulation
function applyManualDiscount(value) {
  document.getElementById("manualDiscount").innerText = value + "%";

  if (!currentData) return;

  const discountedPrice =
    currentData.base_price - (currentData.base_price * value / 100);

  document.getElementById("finalPrice").innerText =
    "₹" + discountedPrice.toFixed(2);

  const profit =
    (discountedPrice - currentData.base_price * 0.9) * currentData.sales;

  document.getElementById("profit").innerText = "₹" + profit.toFixed(0);
}

// Inventory health indicator
function inventoryHealth(d) {
  let health = "Good";
  const box = document.getElementById("statusBox");

  if (d.inventory_status === "STOCK_OUT_RISK") {
    health = "Critical";
    box.className = "status danger";
  } else if (d.inventory_status === "OVERSTOCK_RISK") {
    health = "Excess";
    box.className = "status warning";
  } else {
    box.className = "status safe";
  }

  document.getElementById("healthMeter").innerText = health;
}

// AI discount suggestion badge
function aiDiscountBadge(status) {
  const badge = document.getElementById("aiBadge");
  if (status === "OVERSTOCK_RISK") {
    badge.innerHTML = "🤖 AI Suggests Discount";
    badge.className = "badge";
  } else {
    badge.innerHTML = "";
  }
}

// Charts
function drawCharts(sales, prices) {
  if (salesChart) salesChart.destroy();
  if (priceChart) priceChart.destroy();

  salesChart = new Chart(
    document.getElementById("salesChart"),
    {
      type: "line",
      data: {
        labels: ["D1", "D2", "D3", "D4", "D5"],
        datasets: [{ label: "Sales Trend", data: sales }]
      }
    }
  );

  priceChart = new Chart(
    document.getElementById("priceChart"),
    {
      type: "line",
      data: {
        labels: ["D1", "D2", "D3", "D4", "D5"],
        datasets: [{ label: "Price Trend", data: prices }]
      }
    }
  );
}

// Theme toggle

// Export report
function downloadReport() {
  fetch(`${API}/report`)
    .then(res => res.json())
    .then(msg => alert(msg.message));
}

function toggleTheme() {
    document.body.classList.toggle("dark");

    console.log("Dark mode:", document.body.classList.contains("dark"));
}
