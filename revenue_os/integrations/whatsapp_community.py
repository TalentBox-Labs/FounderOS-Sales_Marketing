"""WhatsApp group/community management for brand building."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid

logger = logging.getLogger(__name__)


class CommunityRole(Enum):
    """Member roles in WhatsApp community."""

    ADMIN = "admin"
    MODERATOR = "moderator"
    MEMBER = "member"
    GUEST = "guest"


class CommunityPurpose(Enum):
    """Community purpose/type."""

    CUSTOMER_SUPPORT = "customer_support"
    USER_COMMUNITY = "user_community"
    FOUNDERS_CIRCLE = "founders_circle"
    PRODUCT_BETA = "product_beta"
    PARTNER_NETWORK = "partner_network"
    SALES_TEAM = "sales_team"
    CUSTOMER_SUCCESS = "customer_success"
    OTHER = "other"


@dataclass
class CommunityMember:
    """Member of WhatsApp community."""

    phone_number: str
    name: str
    role: CommunityRole = CommunityRole.MEMBER
    joined_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_active_at: datetime | None = None
    message_count: int = 0
    invitation_source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "phone_number": self.phone_number,
            "name": self.name,
            "role": self.role.value,
            "joined_at": self.joined_at.isoformat(),
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None,
            "message_count": self.message_count,
        }


@dataclass
class WhatsAppCommunity:
    """WhatsApp group/community."""

    id: str
    name: str
    description: str
    purpose: CommunityPurpose
    group_id: str | None = None  # WhatsApp group ID
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    members: dict[str, CommunityMember] = field(default_factory=dict)
    active: bool = True
    auto_welcome: bool = True
    welcome_message: str = ""
    rules: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "purpose": self.purpose.value,
            "created_at": self.created_at.isoformat(),
            "member_count": len(self.members),
            "active": self.active,
        }


@dataclass
class CommunityPost:
    """Post/update in community."""

    id: str
    community_id: str
    author: str
    content: str
    content_type: str  # text, image, document, link
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reactions: dict[str, int] = field(default_factory=dict)  # emoji -> count
    reply_count: int = 0
    pinned: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "community_id": self.community_id,
            "author": self.author,
            "content": self.content,
            "content_type": self.content_type,
            "created_at": self.created_at.isoformat(),
            "reply_count": self.reply_count,
            "pinned": self.pinned,
        }


class CommunityManager:
    """Manage WhatsApp communities."""

    _communities: dict[str, WhatsAppCommunity] = {}
    _posts: dict[str, CommunityPost] = {}

    @classmethod
    def create_community(
        cls,
        name: str,
        description: str,
        purpose: CommunityPurpose,
        welcome_message: str = "",
        rules: list[str] | None = None,
    ) -> WhatsAppCommunity:
        """Create a new WhatsApp community."""
        community = WhatsAppCommunity(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            purpose=purpose,
            welcome_message=welcome_message,
            rules=rules or [],
        )
        cls._communities[community.id] = community
        logger.info(f"Community created: {community.id} ({name})")
        return community

    @classmethod
    def get_community(cls, community_id: str) -> WhatsAppCommunity | None:
        """Get community by ID."""
        return cls._communities.get(community_id)

    @classmethod
    def list_communities(cls, purpose: CommunityPurpose | None = None) -> list[WhatsAppCommunity]:
        """List communities with optional purpose filter."""
        communities = cls._communities.values()
        if purpose:
            communities = [c for c in communities if c.purpose == purpose]
        return list(communities)

    @classmethod
    def add_member(
        cls,
        community_id: str,
        phone_number: str,
        name: str,
        role: CommunityRole = CommunityRole.MEMBER,
        invitation_source: str = "",
    ) -> CommunityMember | None:
        """Add member to community."""
        community = cls.get_community(community_id)
        if not community:
            logger.error(f"Community not found: {community_id}")
            return None

        member = CommunityMember(
            phone_number=phone_number,
            name=name,
            role=role,
            invitation_source=invitation_source,
        )
        community.members[phone_number] = member
        logger.info(f"Member added to community: {community_id} - {phone_number}")
        return member

    @classmethod
    def remove_member(cls, community_id: str, phone_number: str) -> bool:
        """Remove member from community."""
        community = cls.get_community(community_id)
        if community and phone_number in community.members:
            del community.members[phone_number]
            logger.info(f"Member removed from community: {community_id} - {phone_number}")
            return True
        return False

    @classmethod
    def update_member_role(
        cls, community_id: str, phone_number: str, new_role: CommunityRole
    ) -> bool:
        """Update member role."""
        community = cls.get_community(community_id)
        if community and phone_number in community.members:
            community.members[phone_number].role = new_role
            logger.info(f"Member role updated: {community_id} - {phone_number} → {new_role.value}")
            return True
        return False

    @classmethod
    def record_activity(cls, community_id: str, phone_number: str) -> None:
        """Record member activity."""
        community = cls.get_community(community_id)
        if community and phone_number in community.members:
            member = community.members[phone_number]
            member.last_active_at = datetime.now(timezone.utc)
            member.message_count += 1

    @classmethod
    def create_post(
        cls,
        community_id: str,
        author: str,
        content: str,
        content_type: str = "text",
    ) -> CommunityPost | None:
        """Create a community post."""
        community = cls.get_community(community_id)
        if not community:
            logger.error(f"Community not found: {community_id}")
            return None

        post = CommunityPost(
            id=str(uuid.uuid4()),
            community_id=community_id,
            author=author,
            content=content,
            content_type=content_type,
        )
        cls._posts[post.id] = post
        logger.info(f"Post created in community: {community_id} - {post.id}")
        return post

    @classmethod
    def get_community_posts(
        cls, community_id: str, limit: int = 50, pinned_only: bool = False
    ) -> list[CommunityPost]:
        """Get posts from community."""
        posts = [p for p in cls._posts.values() if p.community_id == community_id]
        if pinned_only:
            posts = [p for p in posts if p.pinned]
        posts.sort(key=lambda p: p.created_at, reverse=True)
        return posts[:limit]

    @classmethod
    def pin_post(cls, post_id: str) -> bool:
        """Pin a post to community."""
        post = cls._posts.get(post_id)
        if post:
            post.pinned = True
            logger.info(f"Post pinned: {post_id}")
            return True
        return False

    @classmethod
    def get_community_stats(cls, community_id: str) -> dict[str, Any]:
        """Get community statistics."""
        community = cls.get_community(community_id)
        if not community:
            return {}

        posts = cls.get_community_posts(community_id)
        total_reactions = sum(sum(p.reactions.values()) for p in posts)
        total_replies = sum(p.reply_count for p in posts)

        # Member role breakdown
        roles = {}
        for member in community.members.values():
            role = member.role.value
            roles[role] = roles.get(role, 0) + 1

        # Active members (last 7 days)
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        active_count = sum(
            1 for m in community.members.values()
            if m.last_active_at and m.last_active_at > cutoff
        )

        return {
            "community_id": community_id,
            "name": community.name,
            "total_members": len(community.members),
            "active_members_7d": active_count,
            "member_roles": roles,
            "total_posts": len(posts),
            "total_reactions": total_reactions,
            "total_replies": total_replies,
            "avg_engagement_per_post": total_reactions / max(len(posts), 1),
        }


class BrandContentStrategy:
    """Manage brand-building content for WhatsApp."""

    _content_calendar: list[dict[str, Any]] = []
    _thought_leadership_posts: list[dict[str, Any]] = []
    _case_studies: list[dict[str, Any]] = []

    @classmethod
    def schedule_founder_post(
        cls,
        founder_name: str,
        content: str,
        scheduled_date: datetime,
        communities: list[str],
        content_type: str = "thought_leadership",
    ) -> str:
        """Schedule founder post across communities."""
        post_id = str(uuid.uuid4())
        post = {
            "id": post_id,
            "founder": founder_name,
            "content": content,
            "scheduled_date": scheduled_date,
            "communities": communities,
            "content_type": content_type,
            "status": "scheduled",
            "created_at": datetime.now(timezone.utc),
        }
        cls._content_calendar.append(post)
        logger.info(f"Founder post scheduled: {post_id}")
        return post_id

    @classmethod
    def add_case_study(
        cls,
        title: str,
        customer_name: str,
        results: str,
        media_urls: list[str] | None = None,
    ) -> str:
        """Add case study for distribution."""
        case_study_id = str(uuid.uuid4())
        case_study = {
            "id": case_study_id,
            "title": title,
            "customer": customer_name,
            "results": results,
            "media": media_urls or [],
            "created_at": datetime.now(timezone.utc),
        }
        cls._case_studies.append(case_study)
        logger.info(f"Case study added: {case_study_id}")
        return case_study_id

    @classmethod
    def get_scheduled_posts(cls, days_ahead: int = 7) -> list[dict[str, Any]]:
        """Get scheduled posts for next N days."""
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) + timedelta(days=days_ahead)
        scheduled = [
            p for p in cls._content_calendar
            if p["scheduled_date"] <= cutoff and p["status"] == "scheduled"
        ]
        return sorted(scheduled, key=lambda p: p["scheduled_date"])

    @classmethod
    def mark_post_sent(cls, post_id: str) -> bool:
        """Mark scheduled post as sent."""
        for post in cls._content_calendar:
            if post["id"] == post_id:
                post["status"] = "sent"
                post["sent_at"] = datetime.now(timezone.utc)
                logger.info(f"Post marked as sent: {post_id}")
                return True
        return False

    @classmethod
    def get_case_studies(cls, limit: int = 10) -> list[dict[str, Any]]:
        """Get all case studies."""
        return cls._case_studies[-limit:]
