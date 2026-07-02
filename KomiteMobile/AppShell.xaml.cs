namespace KomiteMobile;

public partial class AppShell : Shell
{
    public AppShell()
    {
        InitializeComponent();

        Routing.RegisterRoute("community-details", typeof(Views.Community.CommunityDetailsPage));
        Routing.RegisterRoute("community-unit", typeof(Views.Community.UnitPage));
        Routing.RegisterRoute("community-committee", typeof(Views.Community.CommitteePage));
        Routing.RegisterRoute("community-contacts", typeof(Views.Community.UsefulContactsPage));
        Routing.RegisterRoute("profile", typeof(Views.ProfilePage));
        Routing.RegisterRoute("operations-condominiums", typeof(Views.Operations.CondominiumsPage));
        Routing.RegisterRoute("operations-team", typeof(Views.Operations.TeamPage));
        Routing.RegisterRoute("operations-history", typeof(Views.Operations.HistoryPage));
        Routing.RegisterRoute("operations-documents", typeof(Views.Operations.OperationsDocumentsPage));
    }
}
