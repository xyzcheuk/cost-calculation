const PRICES = {
  item1: 10.4,
  item2: 1.5,
  item3: 1.6,
  item4: 98
};

function calculateTotal() {
  var total = 0;
  for (var itemId in PRICES) {
    var qty = parseFloat(document.getElementById(itemId).value);
    var cost = qty * PRICES[itemId];
    total += cost;
    document.getElementById("cost" + itemId.slice(-1)).value = cost.toFixed(2);
  }
  document.getElementById("total").value = total.toFixed(2);
}

function fillempty() {
  for (var itemId in PRICES) {
    var el = document.getElementById(itemId);
    if (el.value === "" || el.value === null) {
      el.value = 0;
    }
  }
}

function main() {
  fillempty();
  calculateTotal();
}

function clearAll() {
  for (var itemId in PRICES) {
    document.getElementById(itemId).value = "";
    document.getElementById("cost" + itemId.slice(-1)).value = "";
  }
  document.getElementById("total").value = "";
}
