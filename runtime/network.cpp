#include <string>
#include <cstring>
#include <curl/curl.h>
#include <sys/socket.h>
#include <netdb.h>
#include <arpa/inet.h>
#include <unistd.h>

static size_t gs_curl_write_callback(void* contents, size_t size, size_t nmemb, std::string* output) {
    output->append((char*)contents, size * nmemb);
    return size * nmemb;
}

extern "C" {
    const char* http_get(const char* url) {
        static std::string result;
        result.clear();
        CURL* curl = curl_easy_init();
        if (curl) {
            curl_easy_setopt(curl, CURLOPT_URL, url);
            curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, gs_curl_write_callback);
            curl_easy_setopt(curl, CURLOPT_WRITEDATA, &result);
            curl_easy_perform(curl);
            curl_easy_cleanup(curl);
        }
        return result.c_str();
    }
    
    int socket_connect(const char* host, int port) {
        int sock = socket(AF_INET, SOCK_STREAM, 0);
        struct hostent* server = gethostbyname(host);
        struct sockaddr_in addr;
        memset(&addr, 0, sizeof(addr));
        addr.sin_family = AF_INET;
        memcpy(&addr.sin_addr.s_addr, server->h_addr, server->h_length);
        addr.sin_port = htons(port);
        connect(sock, (struct sockaddr*)&addr, sizeof(addr));
        return sock;
    }
    
    void socket_send(int sock, const char* data) {
        send(sock, data, strlen(data), 0);
    }
    
    const char* socket_recv(int sock) {
        static char buffer[4096];
        int n = recv(sock, buffer, sizeof(buffer) - 1, 0);
        if (n > 0) { buffer[n] = '\0'; return buffer; }
        return "";
    }
}
