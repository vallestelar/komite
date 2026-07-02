using KomiteMobile.Views;

namespace KomiteMobile.Views.Operations;

public sealed class OperationsMorePage : MenuListPage
{
    public OperationsMorePage()
        : base(
            "Mas",
            "Modo Operacion",
            new[]
            {
                new MenuItemDefinition("Condominios", "operations-condominiums"),
                new MenuItemDefinition("Equipo", "operations-team"),
                new MenuItemDefinition("Historial", "operations-history"),
                new MenuItemDefinition("Documentos operativos", "operations-documents"),
                new MenuItemDefinition("Perfil", "profile"),
                new MenuItemDefinition("Cambiar a Comunidad", "//community-context-selector"),
                new MenuItemDefinition("Cerrar sesion", "logout"),
            })
    {
    }
}
