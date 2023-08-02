<?php
require('creds.php');

// Include config file
$ini = parse_ini_file("config.ini", true);
$student = $ini["users"];
$auth = $ini["authentication"];

if (!isset($student["register"]) || !$student["register"]) {
    header("location: index.php");
    exit;
}

// Define variables and initialize with empty values
$username = $password = $confirm_password = $access_code = "";
$username_err = $password_err = $confirm_password_err = $access_code_err = "";

// Processing form data when form is submitted
if ($_SERVER["REQUEST_METHOD"] == "POST") {

    // Validate username
    if (empty(trim($_POST["username"]))) {
        $username_err = "Please enter a username.";
    } elseif (!preg_match('/^[a-zA-Z0-9_]+$/', trim($_POST["username"]))) {
        $username_err = "Username can only contain letters, numbers, and underscores.";
    } else {
        $username = trim($_POST["username"]);
    }

    // Validate password
    if (empty(trim($_POST["password"]))) {
        $password_err = "Please enter a password.";
    } elseif (strlen(trim($_POST["password"])) < 6) {
        $password_err = "Password must have at least 6 characters.";
    } elseif (strpos($_POST["password"], ",") !== false) {
        $password_err = "Password may not contain a comma.";
    } else {
        $password = trim($_POST["password"]);
    }

    // Validate confirm password
    if (empty(trim($_POST["confirm_password"]))) {
        $confirm_password_err = "Please confirm password.";
    } else {
        $confirm_password = trim($_POST["confirm_password"]);
        if (empty($password_err) && ($password != $confirm_password)) {
            $confirm_password_err = "Password did not match.";
        }
    }

    if (empty(trim($_POST["access_code"]))) {
        $access_code_err = "Please enter access code provided by your instructor.";
    } else {
        $access_code = trim($_POST["access_code"]);
        if ($access_code != $student["access_code"]) {
            $access_code_err = "Invalid access code.";
        }
    }

    // Check input errors before inserting in database
    if (empty($username_err) && empty($password_err) && empty($confirm_password_err) && empty($access_code_err)) {
        $host = $auth["proxmox_host"];
        $user = $auth["proxmox_user"];
        $token_name = $auth["proxmox_token_name"];
        $token_val = $auth["proxmox_token_value"];

        $url = "https://$host/api2/json/access/users";

        $header = array(
            "Authorization: PVEAPIToken=$user!$token_name=$token_val"
        );

        $post = array(
            'userid' => "$username@pve",
            'password' => $password,
            'expire' => 0
        );
        if (isset($student["registrant_groups"])) {
            $post["groups"] = $student["registrant_groups"];
        }
        $post = http_build_query($post);

        $ch = curl_init();

        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_HTTPHEADER, $header);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $post);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);

        $response = curl_exec($ch);

        $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($code == 200) {
            if (isset($student['creds_file'])) {
                add_creds($username, $password, $student['creds_file']);
            }

            header("location: index.php");
            exit;
        } elseif ($code == 500) {
            $username_err = "This username is already taken.";
        } else {
            $register_err = "Failed to register user.";
            //$data = json_decode($response);
            //echo strval($code);
            //print_r($data);
        }
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>Sign Up</title>
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
        <h2>Sign Up</h2>
        <p>Please fill out this form to create an account.</p>

        <?php
        if (!empty($register_err)) {
            echo '<div class="alert alert-danger">' . $register_err . '</div>';
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
                <input type="password" name="password" class="form-control <?php echo (!empty($password_err)) ? 'is-invalid' : ''; ?>" value="<?php echo $password; ?>" />
                <span class="invalid-feedback">
                    <?php echo $password_err; ?>
                </span>
            </div>
            <div class="form-group">
                <label>Confirm Password</label>
                <input type="password" name="confirm_password" class="form-control <?php echo (!empty($confirm_password_err)) ? 'is-invalid' : ''; ?>" value="<?php echo $confirm_password; ?>" />
                <span class="invalid-feedback">
                    <?php echo $confirm_password_err; ?>
                </span>
            </div>
            <div class="form-group">
                <label>Access Code</label>
                <input type="text" name="access_code" class="form-control <?php echo (!empty($access_code_err)) ? 'is-invalid' : ''; ?>" value="<?php echo $access_code; ?>" />
                <span class="invalid-feedback">
                    <?php echo $access_code_err; ?>
                </span>
            </div>

            <div class="form-group">
                <input type="submit" class="btn btn-primary" value="Submit" />
                <input type="reset" class="btn btn-secondary ml-2" value="Reset" />
            </div>
            <p>
                Already have an account? <a href="login.php">Login here</a>.
            </p>
        </form>
    </div>
</body>
</html>