import re
import subprocess

from modules import alerts, geoip, logger, runtime as runtime_mod, state


def monitor_logs():
    firewall_keywords = ("iptables", "nftables", "firewalld", "UFW BLOCK")
    try:
        process = subprocess.Popen(
            ["journalctl", "-f", "-n", "0"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        while True:
            state.update_thread_status("Log Monitor")
            line = process.stdout.readline()
            if not line:
                continue

            runtime = runtime_mod.get_runtime()
            config_data = runtime.config
            detections = config_data["detections"]

            if detections.get("ssh_login", True) and "sshd" in line and (
                "Accepted password" in line or "Accepted publickey" in line
            ):
                user = re.search(r"for (.*?) from", line)
                ip = re.search(r"from (.*?) port", line)
                user_str = user.group(1) if user else "unknown"
                ip_str = ip.group(1) if ip else "unknown"
                geo_info = geoip.lookup_geoip(ip_str, runtime=runtime)
                alerts.send_discord_alert(
                    "SSH Login",
                    user_str,
                    "",
                    "WARNING",
                    f"Successful SSH login for user {user_str}",
                    f"IP: {geo_info}\nLog: {line.strip()}",
                    runtime=runtime
                )

            if detections.get("ssh_failed", True) and "sshd" in line and "Failed password" in line:
                user = re.search(r"Failed password for (?:invalid user )?(\S+)", line)
                ip = re.search(r"from (.*?) port", line)
                user_str = user.group(1) if user else "unknown"
                ip_str = ip.group(1) if ip else "unknown"
                geo_info = geoip.lookup_geoip(ip_str, runtime=runtime)
                alerts.send_discord_alert(
                    "SSH Failed Login",
                    user_str,
                    "",
                    "WARNING",
                    f"Failed SSH login for user {user_str}",
                    f"IP: {geo_info}\nLog: {line.strip()}",
                    runtime=runtime
                )

            if detections.get("sudo", True) and "sudo" in line and "COMMAND=" in line:
                user = re.search(r"\s(\w+)\s*:", line)
                command = re.search(r"COMMAND=(.*)", line)
                user_str = user.group(1) if user else "unknown"
                cmd_str = command.group(1) if command else "unknown"
                alerts.send_discord_alert(
                    "Sudo Usage",
                    user_str,
                    "",
                    "WARNING",
                    f"Sudo command executed by {user_str}",
                    f"Command: {cmd_str}",
                    runtime=runtime
                )

            if detections.get("privilege", True) and "su[" in line and (
                "session opened" in line or "session closed" in line
            ):
                alerts.send_discord_alert(
                    "Privilege Escalation",
                    "",
                    "",
                    "WARNING",
                    "su command activity detected",
                    line.strip(),
                    runtime=runtime
                )

            if detections.get("password_change", True) and "passwd[" in line and (
                "password changed" in line or "authentication token" in line
            ):
                alerts.send_discord_alert(
                    "Password Change",
                    "",
                    "",
                    "WARNING",
                    "passwd command activity detected",
                    line.strip(),
                    runtime=runtime
                )

            if detections.get("kernel", True) and "kernel:" in line and (
                "audit" in line or "IN=" in line or "OUT=" in line
            ):
                alerts.send_discord_alert(
                    "Kernel Alert",
                    "",
                    "",
                    "WARNING",
                    "Kernel reported a security-related message",
                    line.strip(),
                    runtime=runtime
                )

            if detections.get("firewall", True) and any(keyword in line for keyword in firewall_keywords):
                alerts.send_discord_alert(
                    "Firewall Event",
                    "",
                    "",
                    "WARNING",
                    "Firewall log event detected",
                    line.strip(),
                    runtime=runtime
                )

    except Exception as exc:
        logger.log(f"Log monitor failed: {exc}")
