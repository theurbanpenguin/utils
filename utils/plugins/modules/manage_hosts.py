DOCUMENTATION = r'''
---
module: hosts4

short_description: Used to manage /etc/hosts file on Linux and macOS systems

version_added: "0.0.1"

description:
  - This module is used to manage the /etc/hosts file on Linux and macOS systems.
  - By referencing a hostname and IP address pair, entries can be added, modified, or removed.

options:
  hostname:
    description:
      - The hostname to manage in the /etc/hosts file.
    required: true
    type: str
  ip:
    description:
      - The IP address linked with the hostname.
    required: true
    type: str

author:
  - The Urban Penguin (@theurbanpenguin)
'''

EXAMPLES = r'''
- name: Add a hostname entry to /etc/hosts
  hosts4:
    hostname: "server1"
    ip: "192.168.1.10"
    state: present

- name: Remove a hostname entry from /etc/hosts
  hosts4:
    hostname: "server1"
    ip: "192.168.1.10"
    state: absent
'''

RETURN = r'''
message:
  description: A message describing the outcome of the operation.
  returned: always
  type: str
  sample: "Hostname added successfully."

changed:
  description: Whether changes were made to the /etc/hosts file.
  returned: always
  type: bool
  sample: true
'''


# Global variable
HOSTS_FILE = "/etc/hosts"


def run_module():
    from ansible.module_utils.basic import AnsibleModule  # Required for Ansible modules

    module_args = dict(
        hostname=dict(type="str", required=True),  # Hostname to manage
        ip=dict(type="str", required=True),  # IP for the hostname
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )

    result = dict(changed=False, message="")

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    hostname = module.params["hostname"]
    ip = module.params["ip"]
    state = module.params["state"]

    # Track whether specific conditions are met
    found_hostname = False  # Whether the hostname exists
    matching_line_exists = False  # Whether the exact `ip` and `hostname` pair matches

    try:
        global HOSTS_FILE  # Declare global variable for file path

        # Read the contents of the file
        with open(HOSTS_FILE, "r") as file:
            lines = file.readlines()

        # Prepare updated lines for writing back to the file
        updated_lines = []

        for line in lines:
            # Split the line into parts (IP and hostname)
            parts = line.split()
            if len(parts) >= 2:  # Ensure proper line format
                line_ip = parts[0].strip()
                line_hostname = parts[1].strip()

                # Check if the line corresponds to the given hostname
                if line_hostname.lower() == hostname.lower():
                    found_hostname = True
                    if line_ip == ip:
                        # An exact match exists; no changes needed for this line
                        matching_line_exists = True
                        updated_lines.append(line)
                        result["changed"] = False
                        result["message"] = "IP / Hostname pair exist. No changes made."
                    else:
                        # Hostname exists but has a different IP (update required)
                        if state == "present":
                            updated_lines.append(f"{ip}\t{hostname}\n")
                            result["changed"] = True
                            result["message"] = "IP updated for hostname."
                        # Skip this line in the `absent` state (removal case)
                else:
                    # Write back other lines unmodified
                    updated_lines.append(line)

        # If state is "present" and the hostname doesn't exist, add it
        if state == "present" and not found_hostname:
            if not module.check_mode:
                updated_lines.append(f"{ip}\t{hostname}\n")
            result["changed"] = True
            result["message"] = "Hostname added with IP."

        # If state is "absent" and the hostname exists, remove it
        if state == "absent" and found_hostname:
            # Only keep lines that do not match the hostname
            updated_lines = [
                line
                for line in updated_lines
                if not (
                    len(line.split()) >= 2
                    and line.split()[1].strip().lower() == hostname.lower()
                )
            ]
            result["changed"] = True
            result["message"] = "Hostname removed."
        elif state == "absent" and not found_hostname:
            result["message"] = "Hostname does not exist. No changes made."

        # Write the updated lines to the file if not in check mode
        if not module.check_mode:
            with open(HOSTS_FILE, "w") as file:
                file.writelines(updated_lines)

        # Call exit_json to return results
        module.exit_json(**result)

    except FileNotFoundError:
        module.fail_json(msg="The specified path does not exist.")
    except Exception as e:
        module.fail_json(msg=f"An unknown error occurred: {str(e)}")


if __name__ == "__main__":
    run_module()
