using KomiteMobile.Models;

namespace KomiteMobile.Services;

public interface ISessionService
{
    TokenResponse? CurrentSession { get; }

    AppWorkspaceContext? CurrentWorkspace { get; }

    IReadOnlyList<AppWorkspaceContext> CommunityContexts { get; }

    IReadOnlyList<AppWorkspaceContext> OperationsContexts { get; }

    Task SaveAsync(TokenResponse session);

    void SelectWorkspace(AppWorkspaceContext workspace);

    string ResolveInitialRoute();

    Task ClearAsync();
}
