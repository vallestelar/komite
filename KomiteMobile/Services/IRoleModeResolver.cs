using KomiteMobile.Models;

namespace KomiteMobile.Services;

public interface IRoleModeResolver
{
    bool IsCommunityRole(string? roleCode);

    bool IsOperationsRole(string? roleCode, string? companyProfile = null);

    AppMode? ResolveMode(string? roleCode, string? companyProfile = null);
}
