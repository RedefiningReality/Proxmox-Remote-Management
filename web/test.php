<?php

$user = 'test';
$id = 1;

// Parse with sections
require('scripts.php');
[$commands, $logging, $wildcards, $args] = parse_ini();
$logging = [];

// clone options list
$bool_options = [
    'auto_start' => '-s',
    'create_bridge' => '-b',
    'firewall' => '-f'
];

$str_options = [
    'clone_name' => '-c',
    'clone_begin_id' => '-i',
    'clone_type' => '-t',
    'snapshot_name' => '-ss',
    'bridge_subnet' => '-bs',
    'bridge_ports' => '-bp',
    'bridged_vms' => '-bv',
    'cloud-init_static' => '-cs',
    'gateway_ip' => '-fi',
    'dhcp_begin' => '-db',
    'dhcp_end' => '-de',
    'dhcp_dns' => '-dd',
    'dhcp_static' => '-ds'
];

$command = $commands['clone'] . ' ' . $args['ids'] . ' -u ' . $user;
$command = build_command($command, $user, $id, $bool_options, $str_options, $logging, $args, $wildcards);

$clone_command = $command;

// revert options list
$bool_options = [
    'auto_start' => '-s'
];

$str_options = [
    'clone_name' => '-c',
    'snapshot_name' => '-ss'
];

$command = $commands['revert'];
$command = build_command($command, $user, $id, $bool_options, $str_options, $logging, $args, $wildcards);

$revert_command = $command;

// purge options list
$bool_options = [
    'create_bridge' => '-b',
    'firewall' => '-f'
];

$str_options = [
    'bridged_vms' => '-bv'
];

$clone_name = strval($args['clone_name']);
$clone_name = str_replace($wildcards['user'], $user, $clone_name);
$clone_name = str_replace($wildcards['id'], $id, $clone_name);
$command = $commands['purge'] . ' ' . $clone_name;
$command = build_command($command, $user, $id, $bool_options, $str_options, $logging, $args, $wildcards);

$purge_command = $command;

echo "<h2>Commands</h2><b>Clone:</b> <pre>$clone_command</pre>\n<b>Revert:</b> <pre>$revert_command</pre>\n<b>Purge:</b> <pre>$purge_command</pre><hr />";

?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>Test</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" />
</head>
<body>
    <form action="<?php echo htmlspecialchars($_SERVER["PHP_SELF"]); ?>" method="post">
        <input type="submit" name="clone" class="btn btn-success" value="Clone" />
        <input type="submit" name="revert" class="btn btn-warning" value="Revert" />
        <input type="submit" name="purge" class="btn btn-danger" value="Purge" />
    </form>
</body>
</html>

<?php
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    if (isset($_POST['clone'])) {
        $command = $clone_command;
    } elseif (isset($_POST['revert'])) {
        $command = $revert_command;
    } elseif (isset($_POST['purge'])) {
        $command = $purge_command . ' -u';
    }

    echo '<h2>Output</h2>';
    $start = time();
    exec("$command 2>&1", $output, $retval);
    $stop = time();
    $diff = $stop - $start;
    echo "<p><b>Return value:</b> $retval<br><b>Execution time (seconds):</b> $diff</p><pre>";
    print implode("\n", $output);
    echo '</pre>';
}

// echo $var;
// print_r($var);
// var_dump($var);

?>