"""Method for getting sticker from sticker pack."""
from http import HTTPStatus
from urllib.parse import urljoin
from uuid import UUID

from botx.clients.methods.base import AuthorizedBotXMethod
from botx.clients.methods.errors.stickers import sticker_pack_or_sticker_not_found
from botx.clients.types.http import HTTPRequest
from botx.models.stickers import StickerFromPack


class GetSticker(AuthorizedBotXMethod[StickerFromPack]):
    """Method for getting sticker from sticker pack."""

    __url__ = "/api/v3/botx/stickers/packs/{pack_id}/stickers/{sticker_id}"
    __method__ = "GET"
    __returning__ = StickerFromPack
    __errors_handlers__ = {
        HTTPStatus.NOT_FOUND: (sticker_pack_or_sticker_not_found.handle_error,),
    }

    #: sticker pack ID.
    pack_id: UUID

    #: sticker ID.
    sticker_id: UUID

    @property
    def url(self) -> str:
        """Full URL for request with filling pack_id."""
        api_url = self.__url__.format(pack_id=self.pack_id, sticker_id=self.sticker_id)
        return urljoin(super().url, api_url)

    def build_http_request(self) -> HTTPRequest:
        """Build HTTP request that can be used by clients for making real requests.

        Returns:
            Built HTTP request.
        """
        request_params = self.build_serialized_dict()

        return HTTPRequest.construct(
            method=self.http_method,
            url=self.url,
            headers=self.headers,
            query_params=request_params,  # type: ignore
            json_body={},
            expected_type=self.expected_type,
        )