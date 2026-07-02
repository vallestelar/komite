using KomiteMobile.Models;

namespace KomiteMobile.Views;

public sealed class OperationsContextSelectorPage : WorkspaceSelectorPage
{
    public OperationsContextSelectorPage()
        : base(
            AppMode.Operations,
            "Elige condominio",
            "Selecciona el condominio que vas a gestionar en modo operacion.")
    {
    }
}
