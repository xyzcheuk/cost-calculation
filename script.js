const PRICES = {
  item1: 10.4,
  item2: 1.5,
  item3: 1.6,
  item4: 98
};

function calculateTotal() {
  var total = 0;
  for (var itemId in PRICES) {
    var cost;
    if (itemId === "item1") {
      var qty2 = parseFloat(document.getElementById("item2").value);
      var qty3 = parseFloat(document.getElementById("item3").value);
      cost = (qty2 + qty3) * PRICES[itemId];
    } else {
      var qty = parseFloat(document.getElementById(itemId).value);
      cost = qty * PRICES[itemId];
    }
    total += cost;
    document.getElementById("cost" + itemId.slice(-1)).value = cost.toFixed(2);
  }
  document.getElementById("total").value = total.toFixed(2);
}

function fillempty() {
  for (var itemId in PRICES) {
    if (itemId === "item1") continue;
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
    if (itemId === "item1") continue;
    document.getElementById(itemId).value = "";
    document.getElementById("cost" + itemId.slice(-1)).value = "";
  }
  document.getElementById("cost1").value = "";
  document.getElementById("total").value = "";
}
