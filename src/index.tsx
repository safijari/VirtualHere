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
} from "decky-frontend-lib";
import { VFC, useState, useEffect } from "react";
import { VscDebugDisconnect } from "react-icons/vsc";
import logo from "../assets/logo.png";

async function backgroundLoop(serverAPI: ServerAPI): Promise<void> {
    let ret = await serverAPI.callPluginMethod('listener', {});
    if (ret.result == true) {
        Navigation.OpenQuickAccessMenu();
    }
    backgroundLoop(serverAPI);
}

const Content: VFC<{ serverAPI: ServerAPI }> = ({ serverAPI }) => {
    const [enabled, setEnabled] = useState<boolean>(false);

    const onClick = async (e: any) => {
        let res;
        if (e) {
            console.log("enable");
            res = await serverAPI.callPluginMethod('enable_proc', {});
            console.log("enable");
        } else {
            console.log("disable");
            res = await serverAPI.callPluginMethod('disable_proc', {});
            console.log("disable");
        }
        console.log(res);
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
        </PanelSection>
    );
};

export default definePlugin((serverApi: ServerAPI) => {
    console.log("router");
    console.log(Navigation);
    // backgroundLoop(serverApi);
    return {
        title: <div className={staticClasses.Title}>Screentshot Aggregator</div>,
        content: <Content serverAPI={serverApi} />,
        icon: <VscDebugDisconnect />,
        onDismount() {
        },
    };
});