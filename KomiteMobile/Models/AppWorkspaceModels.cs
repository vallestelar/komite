namespace KomiteMobile.Models;

public enum AppMode
{
    Community,
    Operations,
}

public sealed class AppWorkspaceContext
{
    public AppMode Mode { get; init; }

    public CompanyLoginResponse? Company { get; init; }

    public CondominiumLoginResponse Condominium { get; init; } = new();

    public string DisplayName
    {
        get
        {
            if (string.IsNullOrWhiteSpace(Condominium.UnitIdentifier))
            {
                return Condominium.Name;
            }

            return $"{Condominium.Name} / Unidad {Condominium.UnitIdentifier}";
        }
    }
}
