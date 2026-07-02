using KomiteMobile.Views;

namespace KomiteMobile.Views.Community;

public sealed class CommunityMorePage : MenuListPage
{
    public CommunityMorePage()
        : base(
            "Mas",
            "Modo Comunidad",
            new[]
            {
                new MenuItemDefinition("Mi comunidad", "community-details"),
                new MenuItemDefinition("Mi unidad", "community-unit"),
                new MenuItemDefinition("Comite", "community-committee"),
                new MenuItemDefinition("Contactos utiles", "community-contacts"),
                new MenuItemDefinition("Perfil", "profile"),
                new MenuItemDefinition("Cambiar a Operacion", "//operations-context-selector"),
                new MenuItemDefinition("Cerrar sesion", "logout"),
            })
    {
    }
}
