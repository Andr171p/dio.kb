from fastapi import APIRouter, Depends

from src.api.dependencies.auth import get_current_service
from src.api.routers.user.v1 import articles, collections, links, search, spaces

# Service calls currently use a verified legacy admin identity and the same ACL checks as user requests.
router = APIRouter(prefix="/v1", dependencies=[Depends(get_current_service)])
router.add_api_route("/search", search.search_articles, methods=["POST"])
router.add_api_route("/search/suggestions", search.suggest_articles, methods=["POST"])
router.add_api_route("/link-preview", links.get_link_preview, methods=["GET"])
router.add_api_route("/articles/{article_id}", articles.get_published_article, methods=["GET"])
router.add_api_route("/collections/{collection_id}", collections.get_collection, methods=["GET"])
router.add_api_route("/collections/{collection_id}/placements", collections.list_collection_placements, methods=["GET"])
router.add_api_route("/spaces", spaces.list_spaces, methods=["GET"])
router.add_api_route("/spaces/{space_id}", spaces.get_space, methods=["GET"])
router.add_api_route("/spaces/{space_id}/navigation", spaces.get_space_navigation, methods=["GET"])
router.add_api_route("/spaces/{space_id}/articles", spaces.list_space_articles, methods=["GET"])
router.add_api_route("/spaces/{space_id}/articles/{slug}", spaces.get_published_article_by_slug, methods=["GET"])
