<?php

function add_creds($username, $password, $file) {
    $existing = '';
    if (file_exists($file)) {
        $existing = "\n" . file_get_contents($file);
    }

    $entry = "$username,$password";
    file_put_contents($file, $entry . $existing);
}

function update_password($username, $password, $file) {
    $found = false;

    if (file_exists($file)) {
        $data = file_get_contents($file);

        $users = array_map(function ($line) {
            return explode(',', $line);
        }, explode("\n", $data));

        foreach ($users as $i => $user) {
            if ($user[0] == $username) {
                $user[1] = $password;
                $users[$i] = $user;
                $found = true;
            }
        }

        file_put_contents($file, implode("\n", array_map(function ($line) {
            return implode(',', $line);
        }, $users)));
    }

    if (!$found) {
        add_creds($username, $password, $file);
    }
}

?>