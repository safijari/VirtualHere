import {
    ButtonItem,
    definePlugin,
    DialogButton,
    Menu,
    MenuItem,
    PanelSection,
    PanelSectionRow,
    ToggleField,
    Router,
    ServerAPI,
    showContextMenu,
    staticClasses,
    Navigation,
    QuickAccessTab,
} from "decky-frontend-lib";
import { VFC, useState, useEffect } from "react";
import { VscDebugDisconnect } from "react-icons/vsc";
import logo from "../assets/logo.png";

async function backgroundLoop(serverAPI: ServerAPI): Promise<void> {
    let ret = await serverAPI.callPluginMethod('polled_fn', {});
    if (ret.result == true) {
        Navigation.OpenQuickAccessMenu(QuickAccessTab.Decky);
    }
    setTimeout(() => {
        backgroundLoop(serverAPI);
    }, 100)
}

const Content: VFC<{ serverAPI: ServerAPI }> = ({ serverAPI }) => {
    const [enabled, setEnabled] = useState<boolean>(false);

    const onClick = async (e: any) => {
        let res;
        if (e) {
            res = await serverAPI.callPluginMethod('enable_proc', {});
        } else {
            res = await serverAPI.callPluginMethod('disable_proc', {});
        }
    };

    const initState = async () => {
        const getIsEnabledResponse = await serverAPI.callPluginMethod('is_enabled', {});
        setEnabled(getIsEnabledResponse.result as boolean);
    }

    useEffect(() => {
        initState();
    }, []);
    return (
        <PanelSection>
            <PanelSectionRow>
                <ToggleField
                    label="Enable"
                    checked={enabled}
                    onChange={(e) => { onClick(e); }}
                />
            </PanelSectionRow>
            <PanelSectionRow>
            <div>{"While the Deck controller is connected to another computer, it cannot interact with the Deck. Press both volume buttons together to open the QAM menu. If you disable VirtualHere, the controller will be connected back to the Deck."}</div>
            </PanelSectionRow>
            <PanelSectionRow>
            <div>{"WARNING: While VirtualHere is enabled the Deck CANNOT go to sleep. Disable using the switch above when you're done."}</div>
            </PanelSectionRow>
        </PanelSection>
    );
};

export default definePlugin((serverApi: ServerAPI) => {
    backgroundLoop(serverApi);
    return {
        title: <div className={staticClasses.Title}>Screentshot Aggregator</div>,
        content: <Content serverAPI={serverApi} />,
        icon: <VscDebugDisconnect />,
        onDismount() {
        },
        alwaysRender: true,
    };
});