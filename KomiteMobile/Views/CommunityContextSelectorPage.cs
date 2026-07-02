using KomiteMobile.Models;

namespace KomiteMobile.Views;

public sealed class CommunityContextSelectorPage : WorkspaceSelectorPage
{
    public CommunityContextSelectorPage()
        : base(
            AppMode.Community,
            "Elige tu comunidad",
            "Selecciona la comunidad o unidad sobre la que quieres consultar informacion.")
    {
    }
}
