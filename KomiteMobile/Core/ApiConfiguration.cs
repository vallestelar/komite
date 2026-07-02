namespace KomiteMobile.Core;

public static class ApiConfiguration
{
    public static Uri BaseUri
    {
        get
        {
            var host = DeviceInfo.Current.Platform == DevicePlatform.Android
                ? "10.0.2.2"
                : "localhost";

            return new Uri($"http://{host}:8000");
        }
    }
}
