# pdisk-automation-tool
A Python CLI tool to monitor pdisk health, prepare replacements, and automate recovery group operations in storage environments using mmvdisk commands. It provides detailed tabular reports and supports optional email notifications for streamlined disk management.
---

## Features

- Detects and lists problematic pdisks
- Displays pdisk details in a formatted table using `PrettyTable`
- Prepares pdisks for replacement
- Replaces faulty pdisks
- Sends disk status reports via email
- Logs all events and operations to `logs.log`
- Supports dry-run and version info display

---

## Project Structure

```
.
├── replace_email.py    # Main executable script
├── logs.log            # Log file generated during execution
├── output1.txt         # JSON output of pdisk details
├── not_ok_pdisk.txt    # Output of "not ok" pdisks
├── replace_pdisk.txt   # Output of disks marked for replacement
```

---

## Getting Started

### Prerequisites

Ensure the following are installed on your system:

- Python 3.6+
- `mmvdisk` utility available in your environment
- Access to SMTP (for email functionality)

### Install Python dependencies

```bash
pip install pandas docopt prettytable
```

---

## Usage

```bash
python try.py [options]
```

### Options

| Option              | Description                                           |
|---------------------|-------------------------------------------------------|
| `--replace`         | Replace all failed pdisks                             |
| `--prepare`         | Prepare pdisks for replacement                        |
| `--dryrun`          | Show commands that would be executed (no action)      |
| `--email -e <EMAIL>`| Send disk issue summary to an email address           |
| `--version`         | Show script version                                   |
| `-h, --help`        | Show help message                                     |

### Example Commands

```bash
# Show help
python try.py --help

# Run dryrun
python try.py --dryrun

# Prepare and replace disks
python try.py --replace

# Email disk report
python try.py --email -e you@example.com
```

---

## Email Configuration

For the email feature to work, update the following fields in the script (`send_emails` function):

```python
sender_email = "your email address"
sender_password = "your password"
```

You may need to enable "Less secure apps" or use an App Password if using Gmail.

---

## Logging

All operations and command outputs are logged in `logs.log` with timestamps for auditing purposes.

---

## Output Example

The script provides neatly formatted CLI tables for disk statuses like:

```
+-----------+-------------------+--------+----------+----------+----------------+--------+
|   Name    |  RecoveryGroup    | State  | Location | Hardware | User Location  | Server |
+-----------+-------------------+--------+----------+----------+----------------+--------+
| pdisk1    | rg1               | failed | rack2    | SAS      | Floor1         | srv001 |
...
```

---

## Disclaimer

- This tool executes system-level commands. Run it with care and preferably in a test environment first.
- Make sure the `mmvdisk` command works in your shell environment before using this tool.

---


