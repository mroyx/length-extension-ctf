function addToCart(itemId) {
    fetch('/add-to-cart', {
        method: 'POST',
        body: JSON.stringify({ id: itemId }),
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        const msg = document.getElementById("errorMsg");
        msg.textContent = data.message || "Your cart has been updated!";
        msg.className = "text-success mt-3";
    });
}

