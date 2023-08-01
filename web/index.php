<?php
// Initialize the session
session_start();

// Check if the user is logged in, if not then redirect him to login page
if (!isset($_SESSION["loggedin"]) || $_SESSION["loggedin"] !== true) {
    header("location: login.php");
    exit;
}

if (isset($_SESSION["changepwd"]) && $_SESSION["changepwd"] === true) {
    header("location: password.php");
    exit;
}

require('scripts.php');
$ini = parse_ini_file("config.ini", true);
$auth = $ini['authentication'];
$env = $ini['environment'];

$host = $auth['proxmox_host'];
$node = $auth['proxmox_node'];

$proxmox_err = $loading_msg = '';

$url = "https://$host/api2/json/access/ticket";

$username = $_SESSION["user"];
$ticket = $_SESSION["ticket"];
$csrf_token = $_SESSION["csrf"];

//echo "Original ticket: $ticket";
//echo "Original csrf: $csrf_token";

$post = array(
    'username' => "$username@pve",
    'password' => $ticket
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

if ($code == 401) {
    header('Location: login.php');
    exit;
} elseif ($code != 200) {
    $proxmox_err = 'Error connecting to Proxmox.';
    $loading_msg = 'Please try signing out and signing back in again.';
}

if (isset($_SESSION['create'])) {
    if (time() > $_SESSION['create']) {
        unset($_SESSION['create']);
    } else {
        $loading_msg = 'Starting Environment';
        $end = $_SESSION['create'];
    }
} elseif (isset($_SESSION['revert'])) {
    if (time() > $_SESSION['revert']) {
        unset($_SESSION['revert']);
    } else {
        $loading_msg = 'Reverting Environment';
        $end = $_SESSION['revert'];
    }
} elseif (isset($_SESSION['destroy'])) {
    if (time() > $_SESSION['destroy']) {
        unset($_SESSION['destroy']);
    } else {
        $loading_msg = 'Stopping Environment';
        $end = $_SESSION['destroy'];
    }
}

if (empty($loading_msg)) {
    $url = "https://$host/api2/json/nodes/$node/qemu";

    $header = array(
        "Authorization: PVEAuthCookie=$ticket",
        "CSRFPreventionToken: $csrf_token"
    );

    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
    curl_setopt($ch, CURLOPT_HTTPHEADER, $header);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

    $response = curl_exec($ch);
    curl_close($ch);

    $data = json_decode($response)->data;
    $created = !empty($data) || isset($_SESSION["id"]);

    if ($_SERVER["REQUEST_METHOD"] == "POST") {
        if (isset($_POST["create"]) && !$created) {
            $id = proxmox_clone($_SESSION["user"]);
            //$_SESSION["output"] = $output;
            $_SESSION["id"] = $id;

            if (isset($env['create_time'])) {
                $end = time() + $env['create_time'];
                $_SESSION["create"] = $end;
                $loading_msg = 'Starting Environment';
            }
        } elseif (isset($_POST["access"]) && $created) {
            //header("Cookie: PVEAuthCookie=$ticket");
            //header("CSRFPreventionToken: $csrf_token");
            header("Location: https://$host/");
            exit;
        } elseif (isset($_POST['revert']) && $created) {
            proxmox_revert($_SESSION['user'], $_SESSION['id']);

            if (isset($env['revert_time'])) {
                $end = time() + $env['revert_time'];
                $_SESSION["revert"] = $end;
                $loading_msg = 'Reverting Environment';
            }
        } elseif (isset($_POST["destroy"]) && $created) {
            proxmox_purge($_SESSION["user"], $_SESSION["id"]);
            //$_SESSION["output"] = $output;
            unset($_SESSION["id"]);
            $created = false;

            if (isset($env['destroy_time'])) {
                $end = time() + $env['destroy_time'];
                $_SESSION["destroy"] = $end;
                $loading_msg = 'Stopping Environment';
            }
        }
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>Control Panel</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" />
    <style>
        body {
            font: 14px sans-serif;
        }

        .wrapper {
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="wrapper">
        <h2>Control Panel</h2>
        <p><b>User: </b><?php echo htmlspecialchars($_SESSION["user"]); ?></p>

        <?php
        if (!empty($proxmox_err)) {
            echo '<div class="alert alert-danger">' . $proxmox_err . '</div>';
        }
        ?>

        <form action="<?php echo htmlspecialchars($_SERVER["PHP_SELF"]); ?>" method="post">
            <?php
            if (empty($loading_msg)) {
                if (!$created) {
                    echo '<div class="form-group"><input type="submit" name="create" class="btn btn-warning" value="Start" /></div>';
                } else {
                    echo '<div class="form-group"><input type="submit" name="access" class="btn btn-success" value="Access" />';
                    if (isset($env['snapshot_name'])) {
                        echo '<input type="submit" name="revert" class="btn btn-warning ml-3" value="Revert" />';
                    }
                    echo '<input type="submit" name="destroy" class="btn btn-danger ml-3" value="Stop" /></div>';
                }
            } else {
                echo "<p><h5>$loading_msg</h5><div class=\"d-inline\" id=\"loading\"></div></p>";
                if (isset($end)) {
                    echo "<script>var x = setInterval(function() {var end = $end+1;console.log(end);var now = Math.floor(Date.now() / 1000);console.log(now);var seconds = end - now;" .
                        "if (seconds <= 0) {clearInterval(x);window.location.replace('/');} else {document.getElementById(\"loading\").innerHTML = seconds + \" seconds remaining\";}}, 1000);</script>";
                }
            }
            ?>
        </form>

        <p>
            <a href="password.php" class="btn btn-primary">Change Password</a>
            <a href="logout.php" class="btn btn-secondary ml-3">Sign Out</a>
        </p>
        <hr />
        <pre><?php //if (isset($_SESSION["output"])) { echo $_SESSION["output"]; } ?></pre>
    </div>
</body>
</html>