<?php
if ($_SERVER["REQUEST_METHOD"] === "POST") {
    include '../db.php';  // adjust path if your db.php is elsewhere

    $email = $_POST["email"];
    $status = $_POST["status"];

    // Prepare statement to avoid SQL injection
    $stmt = $conn->prepare("UPDATE users SET status=? WHERE email=?");
    $stmt->bind_param("ss", $status, $email);

    if ($stmt->execute()) {
        echo "✅ User status updated to $status.";
    } else {
        echo "❌ Error: " . $stmt->error;
    }

    $stmt->close();
    $conn->close();
}
?>

<h2>Update User Status</h2>
<form method="POST">
  <input type="email" name="email" placeholder="User Email" required><br><br>
  <select name="status" required>
    <option value="paid">Paid</option>
    <option value="unpaid">Unpaid</option>
  </select><br><br>
  <button type="submit">Update Status</button>
</form>
