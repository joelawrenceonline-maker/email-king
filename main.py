"""
email-king CLI.

  python main.py --nudge
      Send the morning draft reminder to NUDGE_TO.

  python main.py --draft --message-id <ID> [--test]
      Stage a draft campaign targeting segment 'joe-favorite'.
      --test uses list 7699 (test audience) instead of list 22 (full audience).

  python main.py --create-message --subject "…" --html-file path/to/file.html
      Create an AC message from an HTML file and print the new message id.

  python main.py --draft --create-message --subject "…" --html-file path/to/file.html [--test]
      Create the message AND stage the draft in one run.

This service never sends a marketing campaign. The only email it sends
is the personal nudge above.
"""
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="email-king")
    parser.add_argument("--nudge", action="store_true", help="Send morning draft reminder")
    parser.add_argument("--draft", action="store_true", help="Stage an AC draft campaign")
    parser.add_argument("--message-id", dest="message_id", help="AC message id to attach")
    parser.add_argument("--create-message", dest="create_message", action="store_true",
                        help="Create an AC message from --html-file and --subject")
    parser.add_argument("--html-file", dest="html_file", help="Path to HTML file for message body")
    parser.add_argument("--subject", dest="subject", help="Email subject line")
    parser.add_argument("--test", action="store_true", help="Target test list 7699 instead of list 22")
    args = parser.parse_args()

    if not (args.nudge or args.draft or args.create_message):
        parser.print_help()
        sys.exit(0)

    if args.nudge:
        from notify import send_morning_nudge
        send_morning_nudge()

    message_id = args.message_id

    if args.create_message:
        if not args.html_file:
            print("[ERROR] --create-message requires --html-file")
            sys.exit(1)
        if not args.subject:
            print("[ERROR] --create-message requires --subject")
            sys.exit(1)

        try:
            with open(args.html_file, encoding="utf-8") as f:
                html = f.read()
        except FileNotFoundError:
            print(f"[ERROR] HTML file not found: {args.html_file}")
            sys.exit(1)

        from message import create_message
        message_id = create_message(subject=args.subject, html=html)
        print(f"Message created -> id={message_id}")

    if args.draft:
        if not message_id:
            print(
                "[ERROR] --draft requires either --message-id or --create-message + --html-file + --subject.\n"
                "This service never invents content — pass a real message id or HTML file."
            )
            sys.exit(1)

        list_id = "7699" if args.test else "22"
        mode = "TEST (list 7699)" if args.test else "PRODUCTION (list 22)"
        print(f"Staging draft in {mode} mode …")

        from segment import find_segment_by_name
        from campaign import create_draft

        segment_id = find_segment_by_name("joe-favorite")
        print(f"Resolved segment 'joe-favorite' -> id={segment_id}")

        subject_label = args.subject or message_id
        campaign_name = f"BCW — {subject_label}"
        campaign_id = create_draft(
            message_id=message_id,
            segment_id=segment_id,
            list_id=list_id,
            name=campaign_name,
        )
        print(f"Done. Campaign {campaign_id} is sitting as a draft in ActiveCampaign.")


if __name__ == "__main__":
    main()
