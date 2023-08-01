<?php

function make_blank_file() {
    $ids = [];
    $serialized = serialize($ids);
    file_put_contents('sessions', $serialized);
}

function read_file() {
    if (!file_exists('sessions')) {
        make_blank_file();
    }

    $serialized = file_get_contents('sessions');
    return unserialize($serialized);
}

function write_file($ids) {
    $serialized = serialize($ids);
    file_put_contents('sessions', $serialized);
}

function add_session() {
    $ids = read_file();

    $id = 1;
    while (in_array($id, $ids)) {
        $id++;
    }

    array_push($ids, $id);
    write_file($ids);

    return $id;
}

function remove_session($id) {
    $ids = read_file();

    $key = array_search($id, $ids);
    unset($ids[$key]);

    write_file($ids);
}

function parse_ini() {
    // Parse with sections
    $ini = parse_ini_file("config.ini", true);

    $commands = $ini['commands'];
    $logging = $ini['logging'];
    $wildcards = $ini['wildcards'];
    $args = $ini['environment'];

    return array($commands, $logging, $wildcards, $args);
}

function build_command($command, $user, $id, $bool_options, $str_options, $logging, $args, $wildcards) {
    // bool options
    foreach ($bool_options as $option_name => $option_cmd) {
        if (array_key_exists($option_name, $args) and $args[$option_name]) {
            $command .= ' ' . $option_cmd;
        }
    }

    // str options
    foreach ($str_options as $option_name => $option_cmd) {
        if (array_key_exists($option_name, $args)) {
            $arg = strval($args[$option_name]);
            $arg = str_replace($wildcards['user'], $user, $arg);
            $arg = str_replace($wildcards['id'], $id, $arg);
            $command .= ' ' . $option_cmd . ' ' . $arg;
        }
    }

    if (isset($logging['info_log'])) {
        $command .= ' >>' . $logging['info_log'];
    }

    if (isset($logging['error_log'])) {
        $command .= ' 2>>' . $logging['error_log'];
    }

    return $command;
}

function proxmox_clone($user) {
    [$commands, $logging, $wildcards, $args] = parse_ini();

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
        'roles' => '-r',
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

    $id = add_session();

    $command = $commands['clone'] . ' ' . $args['ids'] . ' -u ' . $user;
    $command = build_command($command, $user, $id, $bool_options, $str_options, $logging, $args, $wildcards);

    if (substr(php_uname(), 0, 7) == "Windows") {
        pclose(popen("start /B " . $command, "r"));
    } else {
        exec($command . ' &');
    }

    return $id;
}

function proxmox_revert($user, $id) {
    [$commands, $logging, $wildcards, $args] = parse_ini();

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

    if (substr(php_uname(), 0, 7) == "Windows") {
        pclose(popen("start /B " . $command, "r"));
    } else {
        exec($command . ' &');
    }
}

function proxmox_purge($user, $id, $extra='') {
    [$commands, $logging, $wildcards, $args] = parse_ini();

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
    $command = $commands['purge'] . ' ' . $clone_name . $extra;
    $command = build_command($command, $user, $id, $bool_options, $str_options, $logging, $args, $wildcards);

    if (substr(php_uname(), 0, 7) == "Windows") {
        pclose(popen("start /B " . $command, "r"));
    } else {
        exec($command . ' &');
    }

    remove_session($id);
}

?>