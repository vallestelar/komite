using KomiteMobile.Models;

namespace KomiteMobile.Services;

public sealed class RoleModeResolver : IRoleModeResolver
{
    private static readonly HashSet<string> CommunityRoles = new(StringComparer.OrdinalIgnoreCase)
    {
        "vecino",
        "comite",
    };

    private static readonly HashSet<string> OperationsRoles = new(StringComparer.OrdinalIgnoreCase)
    {
        "administrador_empresa",
        "administrador_condominio",
        "supervisor",
        "conserje",
        "superadmin",
    };

    public bool IsCommunityRole(string? roleCode)
    {
        return !string.IsNullOrWhiteSpace(roleCode) && CommunityRoles.Contains(roleCode);
    }

    public bool IsOperationsRole(string? roleCode, string? globalRole = null)
    {
        return (!string.IsNullOrWhiteSpace(roleCode) && OperationsRoles.Contains(roleCode))
            || (!string.IsNullOrWhiteSpace(globalRole) && OperationsRoles.Contains(globalRole));
    }

    public AppMode? ResolveMode(string? roleCode, string? globalRole = null)
    {
        if (IsCommunityRole(roleCode))
        {
            return AppMode.Community;
        }

        if (IsOperationsRole(roleCode, globalRole))
        {
            return AppMode.Operations;
        }

        return null;
    }
}
