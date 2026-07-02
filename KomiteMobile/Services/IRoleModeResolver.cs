using KomiteMobile.Models;

namespace KomiteMobile.Services;

public interface IRoleModeResolver
{
    bool IsCommunityRole(string? roleCode);

    bool IsOperationsRole(string? roleCode, string? globalRole = null);

    AppMode? ResolveMode(string? roleCode, string? globalRole = null);
}
