from .AnimeXin import AnimeXinWebs
from .Animepahe import AnimepaheWebs
from .HanimeTV import HanimeTVWebs
from .Allmanga import AllAnimeWebs
from .anizen import AnizenWebs


web_data = {
  " Animephane ": AnimepaheWebs(),
  " Animexin ": AnimeXinWebs(),
  " Hanime TV ": HanimeTVWebs(),
  " AllManga ": AllAnimeWebs(),
  " Anizen ": AnizenWebs(),
}
web_data = dict(sorted(web_data.items()))
