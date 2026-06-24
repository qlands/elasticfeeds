#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A runnable, end-to-end demonstration of ElasticFeeds (issue #9).

It builds a small network, records a few activities, and then shows the feed being *composed at read time*
by different aggregators -- including the pagination patterns people expect from hosted services such as
GetStream.

GetStream            ->  ElasticFeeds
---------------------    ----------------------------------------------------
feed.get(limit, offset)  Manager.get_feeds(UnAggregated(actor, result_size=, result_from=))
feed.get(id_lt=...)      Manager.get_feeds(CursorAggregator(actor, search_after=...))
feed.add_activity(...)   Manager.add_activity_feed(Activity(...))

Usage:
    export ES_HOST=192.168.0.12 ES_PORT=9200 ES_USER=elastic ES_PASS=secret
    # optional: export EF_BACKEND=opensearch   (requires: pip install elasticfeeds[opensearch])
    python examples/demo.py

It uses throwaway indices (ef_demo_*) and deletes them at the end, so it will not touch your data.
"""

import datetime
import json
import os

from elasticfeeds.manager import Manager
from elasticfeeds.activity import Actor, Object, Activity
from elasticfeeds.aggregators import (
    UnAggregated,
    CursorAggregator,
    NotificationAggregator,
    DecayRankedAggregator,
)


def show(title, data):
    print("\n" + "=" * 78 + f"\n{title}\n" + "-" * 78)
    print(json.dumps(data, indent=2, default=str))


def main():
    now = datetime.datetime.now()

    manager = Manager(
        feed_index="ef_demo_feeds",
        network_index="ef_demo_network",
        host=os.environ.get("ES_HOST", "localhost"),
        port=int(os.environ.get("ES_PORT", "9200")),
        user_name=os.environ.get("ES_USER", "elastic"),
        user_password=os.environ.get("ES_PASS", ""),
        backend=os.environ.get("EF_BACKEND", "elasticsearch"),
        delete_feeds_if_exists=True,
        delete_network_if_exists=True,
    )
    print(f"Connected using the '{manager.backend}' backend.")

    try:
        # 1) Build carlos's network: follow two people, watch a project.
        manager.follow("carlos", "mark", linked=now - datetime.timedelta(days=1))
        manager.follow("carlos", "jane", linked=now - datetime.timedelta(days=1))
        manager.watch(
            "carlos", "project_a", "project", linked=now - datetime.timedelta(days=1)
        )

        # 2) Record some activities (most recent last).
        activities = [
            Activity(
                "add",
                Actor("mark", "person"),
                Object("project_a", "project"),
                published=now - datetime.timedelta(hours=5),
            ),
            Activity(
                "add",
                Actor("jane", "person"),
                Object("project_a", "project"),
                published=now - datetime.timedelta(hours=4),
            ),
            Activity(
                "blog",
                Actor("mark", "person"),
                Object("project_a", "project"),
                published=now - datetime.timedelta(hours=3),
            ),
            Activity(
                "comment",
                Actor("jane", "person"),
                Object("project_b", "project"),
                published=now - datetime.timedelta(hours=2),
            ),
            Activity(
                "add",
                Actor("mark", "person"),
                Object("project_a", "project"),
                published=now - datetime.timedelta(hours=1),
            ),
        ]
        for activity in activities:
            manager.add_activity_feed(activity)

        # Feeds are near-real-time; refresh so the demo sees the writes immediately.
        manager.connection.indices.refresh(index="ef_demo_feeds")
        manager.connection.indices.refresh(index="ef_demo_network")

        # 3) Chronological feed (GetStream: feed.get()).
        chronological = manager.get_feeds(UnAggregated("carlos"))
        show(f"Chronological feed ({len(chronological)} activities)", chronological)

        # 4) limit/offset pagination (GetStream: feed.get(limit, offset)).
        page = UnAggregated("carlos")
        page.result_size = 2
        page.result_from = 0
        show("limit=2, offset=0", manager.get_feeds(page))

        # 5) Cursor / infinite scroll (GetStream: feed.get(id_lt=...)).
        cur = CursorAggregator("carlos")
        cur.result_size = 2
        first = manager.get_feeds(cur)
        show("Cursor page 1 (size 2)", first)
        if first["next_cursor"]:
            second = manager.get_feeds(
                CursorAggregator("carlos", search_after=first["next_cursor"])
            )
            show("Cursor page 2 (via next_cursor)", second)

        # 6) Notification-style summaries.
        show("Notifications", manager.get_feeds(NotificationAggregator("carlos")))

        # 7) Ranked ("hot") feed.
        show("Decay-ranked feed", manager.get_feeds(DecayRankedAggregator("carlos")))

        # 8) Graph introspection, independent of the network (issue #8).
        show(
            "get_activities(actor_id='mark', verb='add')",
            manager.get_activities(actor_id="mark", verb="add"),
        )

    finally:
        manager.delete_feeds_index()
        manager.delete_network_index()
        print("\nCleaned up demo indices.")


if __name__ == "__main__":
    main()
