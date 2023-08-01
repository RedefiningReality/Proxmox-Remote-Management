<?php
// Initialize the session
session_start();

// Check if the user is already logged in, if yes then redirect them to welcome page
if (isset($_SESSION["loggedin"]) && $_SESSION["loggedin"] === true) {
    header("location: index.php");
    exit;
}

$ini = parse_ini_file("config.ini", true);
$auth = $ini['authentication'];
$student = $ini['users'];

// Define variables and initialize with empty values
$username = $password = "";
$username_err = $password_err = $login_err = "";

// Processing form data when form is submitted
if ($_SERVER["REQUEST_METHOD"] == "POST") {

    // Check if username is empty
    if (empty(trim($_POST["username"]))) {
        $username_err = "Please enter username.";
    } else {
        $username = trim($_POST["username"]);
    }

    // Check if password is empty
    if (empty(trim($_POST["password"]))) {
        $password_err = "Please enter your password.";
    } else {
        $password = trim($_POST["password"]);
    }

    // Validate credentials
    if (empty($username_err) && empty($password_err)) {
        $host = $auth['proxmox_host'];
        $bad_password = $student['change_password'];

        $url = "https://$host/api2/json/access/ticket";

        $post = array(
            'username' => "$username@pve",
            'password' => $password
        );
        $post = http_build_query($post);

        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $post);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

        $response = curl_exec($ch);

        $code = curl_getinfo($ch, CURLINFO_HTTP_CODE); // 401 code is bad login - 200 is good
        curl_close($ch);

        if ($code == 200) {
            $data = json_decode($response)->data;
            $ticket = $data->ticket;
            $csrf_token = $data->CSRFPreventionToken;

            // Store data in session variables
            $_SESSION["loggedin"] = true;
            $_SESSION["user"] = $username;
            $_SESSION["ticket"] = $ticket;
            $_SESSION["csrf"] = $csrf_token;

            if ($password == $bad_password) {
                // Redirect user to change password page
                $_SESSION["changepwd"] = true;
                header("location: password.php");
                exit;
            } else {
                // Redirect user to main page
                header("location: index.php");
                exit;
            }

        } elseif ($code == 401) {
            $login_err = "Invalid username or password.";
        } else {
            $login_err = "Error connecting to Proxmox. Please contact administrator.";
        }
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>Login</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" />
    <style>
        body {
            font: 14px sans-serif;
        }
        .wrapper {
            width: 360px;
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="wrapper">
        <h2>Login</h2>
        <p>Please fill in your credentials to login.</p>

        <?php
        if (!empty($login_err)) {
            echo '<div class="alert alert-danger">' . $login_err . '</div>';
        }
        ?>

        <form action="<?php echo htmlspecialchars($_SERVER["PHP_SELF"]); ?>" method="post">
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="username" class="form-control <?php echo (!empty($username_err)) ? 'is-invalid' : ''; ?>" value="<?php echo $username; ?>" />
                <span class="invalid-feedback">
                    <?php echo $username_err; ?>
                </span>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" class="form-control <?php echo (!empty($password_err)) ? 'is-invalid' : ''; ?>" />
                <span class="invalid-feedback">
                    <?php echo $password_err; ?>
                </span>
            </div>
            <div class="form-group">
                <input type="submit" class="btn btn-primary" value="Login" />
            </div>
            <?php
            $ini = parse_ini_file("config.ini", true);
            $student = $ini["users"];
            if (isset($student["register"]) && $student["register"]) {
                echo '<p>Don\'t have an account? <a href="register.php">Sign up now</a>.</p>';
            }
            ?>
        </form>
    </div>
</body>
</html>