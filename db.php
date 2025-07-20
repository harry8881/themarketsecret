<?php
// Optional: Use environment variables if deploying to Render later
$host = getenv("DB_HOST") ?: "sql12.freesqldatabase.com";
$dbname = getenv("DB_NAME") ?: "sql12790966";
$username = getenv("DB_USER") ?: "sql12790966";
$password = getenv("DB_PASS") ?: "wdNQVclgnT";

// Connect to MySQL
$conn = new mysqli($host, $username, $password, $dbname);

// Check connection
if ($conn->connect_error) {
    die("❌ Connection failed: " . $conn->connect_error);
}

// echo "✅ Connected successfully";
?>
