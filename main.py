"""
email-king CLI.

  python main.py --nudge
      Send the morning draft reminder to NUDGE_TO.

  python main.py --draft --message-id <ID> [--test]
      Stage a draft campaign targeting segment 'joe-favorite'.
      --test uses list 7699 (test audience) instead of list 22 (full audience).

This service never sends a marketing campaign. The only email it sends
is the personal nudge above. It will refuse to run --draft without a message id.
"""
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="email-king")
    parser.add_argument("--nudge", action="store_true", help="Send morning draft reminder")
    parser.add_argument("--draft", action="store_true", help="Stage an AC draft campaign")
    parser.add_argument("--message-id", dest="message_id", help="AC message id to attach")
    parser.add_argument("--test", action="store_true", help="Target test list 7699 instead of list 22")
    args = parser.parse_args()

    if not (args.nudge or args.draft):
        parser.print_help()
        sys.exit(0)

    if args.nudge:
        from notify import send_morning_nudge
        send_morning_nudge()

    if args.draft:
        if not args.message_id:
            print(
                "[ERROR] --draft requires --message-id. "
                "This service never invents content — pass a real message id."
            )
            sys.exit(1)

        list_id = "7699" if args.test else "22"
        mode = "TEST (list 7699)" if args.test else "PRODUCTION (list 22)"
        print(f"Staging draft in {mode} mode …")

        from segment import find_segment_by_name
        from campaign import create_draft

        segment_id = find_segment_by_name("joe-favorite")
        print(f"Resolved segment 'joe-favorite' → id={segment_id}")

        campaign_name = f"BCW Draft — msg {args.message_id}"
        campaign_id = create_draft(
            message_id=args.message_id,
            segment_id=segment_id,
            list_id=list_id,
            name=campaign_name,
        )
        print(f"Done. Campaign {campaign_id} is sitting as a draft in ActiveCampaign.")


if __name__ == "__main__":
    main()
