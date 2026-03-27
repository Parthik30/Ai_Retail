fetch("/api/dashboard")
  .then(res => res.json())
  .then(d => {
    document.getElementById("sales").innerText = "₹" + d.total_sales;
    document.getElementById("units").innerText = d.units_sold;
    document.getElementById("avgPrice").innerText = "₹" + d.avg_price;
    document.getElementById("turnover").innerText = d.inventory_turnover;

    drawStockChart(d.stock_available, d.reorder_qty);
    showTopProducts();
  });

function drawStockChart(stock, reorder) {
  new Chart(document.getElementById("stockChart"), {
    type: "bar",
    data: {
      labels: ["Available Stock", "Reorder Qty"],
      datasets: [{
        label: "Stock Info",
        data: [stock, reorder],
        backgroundColor: ["#4c6fff", "#f39c12"]
      }]
    }
  });
}

function showTopProducts() {
  const list = document.getElementById("topProducts");
  list.innerHTML = "";
  ["Laptop", "Phone", "Earbuds", "Monitor", "Keyboard"].forEach(p => {
    const li = document.createElement("li");
    li.innerText = p + " – High Demand";
    list.appendChild(li);
  });
}

function loadProducts() {
  fetch("/api/products")
    .then(res => res.json())
    .then(products => {
      const select = document.getElementById("productSelect");
      products.forEach(p => {
        const opt = document.createElement("option");
        opt.value = p;
        opt.textContent = p;
        select.appendChild(opt);
      });
    });
}

function loadProductData() {
  const product = document.getElementById("productSelect").value;
  if (!product) return;

  fetch(`/api/dashboard?product=${encodeURIComponent(product)}`)
    .then(res => res.json())
    .then(d => {
      document.getElementById("sales").innerText = "₹" + d.total_sales;
      document.getElementById("units").innerText = d.units_sold;
      document.getElementById("avgPrice").innerText = "₹" + d.avg_price;
      document.getElementById("turnover").innerText = d.inventory_turnover;

      drawStockChart(d.stock_available, d.reorder_qty);
    });
}

window.onload = () => {
  loadProducts();
};
let stockChart = null;

function loadProductData() {
  const product = document.getElementById("productSelect").value;
  if (!product) return;

  fetch(`/api/dashboard?product=${encodeURIComponent(product)}`)
    .then(res => res.json())
    .then(d => {

      // KPI updates
      document.getElementById("sales").innerText = d.sales;
      document.getElementById("units").innerText = d.sales;
      document.getElementById("avgPrice").innerText = "₹" + d.final_price;
      document.getElementById("turnover").innerText = d.inventory_turnover;

      // 🔥 STOCK INFO CHART
      drawStockChart(d.stock_available, d.reorder_qty);
    });
}

function drawStockChart(stock, reorder) {

  // Destroy old chart
  if (stockChart) {
    stockChart.destroy();
  }

  stockChart = new Chart(
    document.getElementById("stockChart").getContext("2d"),
    {
      type: "bar",
      data: {
        labels: ["Available Stock", "Reorder Qty"],
        datasets: [{
          label: "Stock Info",
          data: [stock, reorder],
          backgroundColor: ["#4c6fff", "#f39c12"]
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: true }
        }
      }
    }
  );
}
