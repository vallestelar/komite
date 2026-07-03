using System.Text.Json;
using KomiteMobile.Models;

namespace KomiteMobile.Services;

public sealed class SessionService : ISessionService
{
    private const string SessionKey = "komite_session";
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);
    private readonly IRoleModeResolver _roleModeResolver;

    private List<AppWorkspaceContext> _communityContexts = [];
    private List<AppWorkspaceContext> _operationsContexts = [];

    public SessionService(IRoleModeResolver roleModeResolver)
    {
        _roleModeResolver = roleModeResolver;
    }

    public TokenResponse? CurrentSession { get; private set; }

    public AppWorkspaceContext? CurrentWorkspace { get; private set; }

    public IReadOnlyList<AppWorkspaceContext> CommunityContexts => _communityContexts;

    public IReadOnlyList<AppWorkspaceContext> OperationsContexts => _operationsContexts;

    public async Task SaveAsync(TokenResponse session)
    {
        CurrentSession = session;
        BuildContexts(session);
        var payload = JsonSerializer.Serialize(session, JsonOptions);
        await SecureStorage.Default.SetAsync(SessionKey, payload);
    }

    public void SelectWorkspace(AppWorkspaceContext workspace)
    {
        CurrentWorkspace = workspace;
    }

    public string ResolveInitialRoute()
    {
        var hasCommunity = CommunityContexts.Count > 0;
        var hasOperations = OperationsContexts.Count > 0;

        if (hasCommunity && hasOperations)
        {
            return "//mode-selector";
        }

        if (hasCommunity)
        {
            if (CommunityContexts.Count == 1)
            {
                SelectWorkspace(CommunityContexts[0]);
                return "//community";
            }

            return "//community-context-selector";
        }

        if (hasOperations)
        {
            return "//operations-context-selector";
        }

        return "//mode-selector";
    }

    public Task ClearAsync()
    {
        CurrentSession = null;
        CurrentWorkspace = null;
        _communityContexts = [];
        _operationsContexts = [];
        SecureStorage.Default.Remove(SessionKey);
        return Task.CompletedTask;
    }

    private void BuildContexts(TokenResponse session)
    {
        _communityContexts = [];
        _operationsContexts = [];
        CurrentWorkspace = null;
        var communityContexts = new Dictionary<string, AppWorkspaceContext>(StringComparer.OrdinalIgnoreCase);
        var operationsContexts = new Dictionary<string, AppWorkspaceContext>(StringComparer.OrdinalIgnoreCase);

        foreach (var condominium in session.Condominiums)
        {
            if (_roleModeResolver.IsCommunityRole(condominium.Role))
            {
                var key = $"{condominium.Id}:{condominium.UnitId}";
                communityContexts.TryAdd(
                    key,
                    CreateWorkspace(AppMode.Community, session.Company, condominium));
            }

            var hasExplicitOperationsRole = _roleModeResolver.IsOperationsRole(condominium.Role);
            var hasGlobalOperationsRole = _roleModeResolver.IsOperationsRole(null, session.User.CompanyProfile);
            if (hasExplicitOperationsRole || hasGlobalOperationsRole)
            {
                var key = condominium.Id;
                var workspace = CreateWorkspace(AppMode.Operations, session.Company, condominium);
                if (!operationsContexts.TryGetValue(key, out var existing))
                {
                    operationsContexts[key] = workspace;
                    continue;
                }

                var existingIsExplicitOperationsRole = _roleModeResolver.IsOperationsRole(existing.Condominium.Role);
                if (hasExplicitOperationsRole && !existingIsExplicitOperationsRole)
                {
                    operationsContexts[key] = workspace;
                }
            }
        }

        _communityContexts = communityContexts.Values.ToList();
        _operationsContexts = operationsContexts.Values.ToList();
    }

    private static AppWorkspaceContext CreateWorkspace(
        AppMode mode,
        CompanyLoginResponse? company,
        CondominiumLoginResponse condominium)
    {
        return new AppWorkspaceContext
        {
            Mode = mode,
            Company = company,
            Condominium = condominium,
        };
    }
}
