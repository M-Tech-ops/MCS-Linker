#include "NBT_explorer.hpp"

int main(int argc, char* argv[]) {
    std::string path{argv[1]};

    NBTExplorer explorer;

    if (!explorer.LoadWorld(path)) {
        size_t pos = path.find_last_of("/\\");

        std::string filename =
            (pos == std::string::npos)
                ? path
                : path.substr(pos + 1);

        std::cerr << "CRITICAL ERROR: Failed to load " << filename << "!" << std::endl;
        return 1;
    }

    auto CurrentFolder = explorer.GetMasterDataMap();

    if (!CurrentFolder) {
        std::cerr << "CRITICAL ERROR: Could not locate master Data map." << std::endl;
        return 1;
    }

    std::cout << NBTExplorer::ReadRawValue(CurrentFolder, "LevelName") << "," <<
        NBTExplorer::ReadRawValue(CurrentFolder, "Time") << "," <<
        NBTExplorer::ReadRawValue(CurrentFolder, "LastPlayed") << "," <<
        NBTExplorer::ReadRawValue(CurrentFolder, "DataVersion")<< std::endl;
        return 0;
}
