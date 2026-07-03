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
        "supervisor",
        "conserje",
    };

    private static readonly HashSet<string> OperationsProfiles = new(StringComparer.OrdinalIgnoreCase)
    {
        "project_manager",
        "ejecutivo",
    };

    public bool IsCommunityRole(string? roleCode)
    {
        return !string.IsNullOrWhiteSpace(roleCode) && CommunityRoles.Contains(roleCode);
    }

    public bool IsOperationsRole(string? roleCode, string? companyProfile = null)
    {
        return (!string.IsNullOrWhiteSpace(roleCode) && OperationsRoles.Contains(roleCode))
            || (!string.IsNullOrWhiteSpace(companyProfile) && OperationsProfiles.Contains(companyProfile));
    }

    public AppMode? ResolveMode(string? roleCode, string? companyProfile = null)
    {
        if (IsCommunityRole(roleCode))
        {
            return AppMode.Community;
        }

        if (IsOperationsRole(roleCode, companyProfile))
        {
            return AppMode.Operations;
        }

        return null;
    }
}
